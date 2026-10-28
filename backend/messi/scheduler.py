"""Deterministic serial schedule generation and a separate engineering validator.

Splittable mining activities, exclusive resources, same-day shifts, no reclaim.
This method finds a feasible baseline; it does not prove global optimality.
"""

from __future__ import annotations
from datetime import datetime, date, time, timedelta, timezone
from collections import defaultdict
from zoneinfo import ZoneInfo
import math
from .domain import Inputs, DomainError

UTC = timezone.utc
VERSION = "messi-baseline-0.1.0"


def instant(value):
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        raise DomainError("Timestamp requires an explicit UTC offset")
    return dt.astimezone(UTC)


def locked_time(block, cfg):
    if not block.locked_start:
        return None
    if len(block.locked_start) == 10:
        return datetime.combine(
            date.fromisoformat(block.locked_start),
            time(cfg.calendar.shift_start),
            ZoneInfo(cfg.timezone),
        ).astimezone(UTC)
    return instant(block.locked_start)


def working_windows(cfg, resource):
    start = date.fromisoformat(cfg.calendar.start)
    tz = ZoneInfo(cfg.timezone)
    for i in range(cfg.calendar.days):
        day = start + timedelta(days=i)
        if day.weekday() not in cfg.calendar.weekdays or day.isoformat() in resource.outages:
            continue
        lo = datetime.combine(day, time(cfg.calendar.shift_start), tz)
        hi = lo + timedelta(hours=cfg.calendar.shift_hours)
        yield lo.astimezone(UTC), hi.astimezone(UTC)


def graph_issues(cfg):
    # Iterative topological pass handles the full 2,000-activity import limit.
    from collections import deque

    indegree = {b.id: len(b.predecessors) for b in cfg.blocks}
    children = defaultdict(list)
    for b in cfg.blocks:
        for pred in b.predecessors:
            children[pred].append(b.id)
    ready = deque(sorted(bid for bid, n in indegree.items() if not n))
    while ready:
        bid = ready.popleft()
        for child in children[bid]:
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
    blocked = sorted(bid for bid, n in indegree.items() if n)
    return (
        ["Precedence cycle or downstream cycle blockage: " + ", ".join(blocked)] if blocked else []
    )


def propose(cfg, b, r, earliest, reservations):
    """Return finite split allocations using free intervals, without mutating state."""
    rate = r.rate * r.utilization
    remaining = b.tonnes
    result = []
    locked = locked_time(b, cfg)
    for low, high in working_windows(cfg, r):
        low = max(low, earliest)
        if low >= high:
            continue
        free = [(low, high)]
        for used_low, used_high in sorted(reservations):
            next_free = []
            for a, z in free:
                if used_high <= a or used_low >= z:
                    next_free.append((a, z))
                    continue
                if a < used_low:
                    next_free.append((a, used_low))
                if used_high < z:
                    next_free.append((used_high, z))
            free = next_free
        for a, z in free:
            if locked is not None and not result:
                if locked < a or locked >= z:
                    continue
                a = locked
            quantity = min(remaining, (z - a).total_seconds() / 3600 * rate)
            if quantity <= 1e-8:
                continue
            end = a + timedelta(hours=quantity / rate)
            result.append(
                {
                    "block_id": b.id,
                    "resource_id": r.id,
                    "destination": b.destination,
                    "start": a.isoformat(),
                    "end": end.isoformat(),
                    "tonnes": quantity,
                    "hours": quantity / rate,
                    "material": b.material,
                    "basis": b.basis,
                    "ash": b.ash,
                }
            )
            remaining -= quantity
            if remaining <= 1e-6:
                return result
    return None


def schedule(data, progress=lambda _x: None):
    cfg = Inputs.model_validate(data)
    issues = graph_issues(cfg)
    if issues:
        return {
            "status": "no_plan_found",
            "engine": VERSION,
            "allocations": [],
            "activities": [],
            "violations": issues,
            "stocks": [],
            "periods": [],
            "totals": {"tonnes": 0, "coal": 0, "waste": 0, "volume": 0},
            "unscheduled": [
                {"id": b.id, "reason": "Precedence graph contains a cycle"} for b in cfg.blocks
            ],
        }
    resources = sorted(cfg.resources, key=lambda r: r.id)
    used = defaultdict(list)
    done = {}
    allocations = []
    unscheduled = []
    remaining = {b.id: b for b in cfg.blocks}
    stock = {d.id: d.opening for d in cfg.destinations}
    destinations = {d.id: d for d in cfg.destinations}
    horizon = datetime.combine(
        date.fromisoformat(cfg.calendar.start), time.min, ZoneInfo(cfg.timezone)
    ).astimezone(UTC)
    while remaining:
        eligible = [b for b in remaining.values() if all(p in done for p in b.predecessors)]
        if not eligible:
            unscheduled += [
                {"id": bid, "reason": "Predecessor is unscheduled"} for bid in sorted(remaining)
            ]
            break
        b = min(eligible, key=lambda b: (b.priority, b.id))
        earliest = max([horizon] + [done[p] for p in b.predecessors])
        lock = locked_time(b, cfg)
        reason = None
        if lock and lock < earliest:
            reason = "Locked start is earlier than predecessor completion / horizon"
        if stock[b.destination] + b.tonnes > destinations[b.destination].capacity + 1e-6:
            reason = "Destination capacity exceeded; this release does not model reclaim"
        candidates = []
        if not reason:
            for r in resources:
                if b.material not in r.materials or (
                    b.locked_resource and b.locked_resource != r.id
                ):
                    continue
                plan = propose(cfg, b, r, earliest, used[r.id])
                if plan:
                    candidates.append((plan[-1]["end"], r.id, plan))
        if candidates:
            _, rid, plan = min(candidates, key=lambda x: (x[0], x[1]))
            allocations.extend(plan)
            used[rid].extend((instant(a["start"]), instant(a["end"])) for a in plan)
            done[b.id] = instant(plan[-1]["end"])
            stock[b.destination] += b.tonnes
        else:
            unscheduled.append(
                {
                    "id": b.id,
                    "reason": reason
                    or "No compatible resource/calendar slot within horizon (heuristic result, not infeasibility proof)",
                }
            )
        del remaining[b.id]
        progress(int(100 * (len(cfg.blocks) - len(remaining)) / max(1, len(cfg.blocks))))
    activity = []
    for b in cfg.blocks:
        items = [a for a in allocations if a["block_id"] == b.id]
        activity.append(
            {
                "id": b.id,
                "start": min((a["start"] for a in items), default=None),
                "end": max((a["end"] for a in items), default=None),
                "tonnes": sum(a["tonnes"] for a in items),
                "hours": sum(a["hours"] for a in items),
                "complete": b.id in done,
            }
        )
    periods = defaultdict(lambda: {"coal": 0.0, "waste": 0.0})
    for a in allocations:
        day = instant(a["start"]).astimezone(ZoneInfo(cfg.timezone)).date().isoformat()
        periods[day][a["material"]] += a["tonnes"]
    stocks = []
    for d in cfg.destinations:
        items = [a for a in allocations if a["destination"] == d.id]
        received = sum(a["tonnes"] for a in items)
        closing = d.opening + received
        ash = (
            (sum(a["tonnes"] * (a["ash"] or 0) for a in items) + d.opening * (d.opening_ash or 0))
            / closing
            if closing and d.material == "coal"
            else None
        )
        stocks.append(
            {
                "id": d.id,
                "name": d.name,
                "material": d.material,
                "basis": d.basis,
                "opening": d.opening,
                "receipts": received,
                "reclaim": 0.0,
                "loss": 0.0,
                "closing": closing,
                "capacity": d.capacity,
                "ash": ash,
            }
        )
    result = {
        "status": "feasible" if not unscheduled else "partial",
        "engine": VERSION,
        "allocations": sorted(
            allocations, key=lambda a: (a["start"], a["resource_id"], a["block_id"])
        ),
        "activities": activity,
        "unscheduled": unscheduled,
        "stocks": stocks,
        "periods": [{"date": d, **p} for d, p in sorted(periods.items())],
        "totals": {
            "tonnes": sum(a["tonnes"] for a in allocations),
            "coal": sum(a["tonnes"] for a in allocations if a["material"] == "coal"),
            "waste": sum(a["tonnes"] for a in allocations if a["material"] == "waste"),
            "volume": sum(b.volume for b in cfg.blocks if b.id in done),
        },
        "violations": [],
    }
    result["violations"] = validate_result(data, result)
    if result["violations"]:
        result["status"] = "invalid"
    return result


def validate_result(data, result):
    """Independent checks: no reuse of the heuristic's free-slot allocator."""
    cfg = Inputs.model_validate(data)
    blocks = {b.id: b for b in cfg.blocks}
    resources = {r.id: r for r in cfg.resources}
    dest = {d.id: d for d in cfg.destinations}
    errors = []
    by_block = defaultdict(list)
    by_resource = defaultdict(list)
    received = defaultdict(float)
    close = lambda a, b: math.isclose(a, b, rel_tol=1e-8, abs_tol=1e-4)
    for a in result.get("allocations", []):
        try:
            b = blocks[a["block_id"]]
            r = resources[a["resource_id"]]
            low, high = instant(a["start"]), instant(a["end"])
            q = a["tonnes"]
            if not math.isfinite(q) or q <= 0 or high <= low:
                errors.append(f"{b.id}: invalid time/quantity")
                continue
            if not close(q, (high - low).total_seconds() / 3600 * r.rate * r.utilization):
                errors.append(f"{b.id}: rate/time mismatch")
            if b.material not in r.materials:
                errors.append(f"{b.id}: incompatible resource")
            if b.locked_resource and r.id != b.locked_resource:
                errors.append(f"{b.id}: resource lock violated")
            local = low.astimezone(ZoneInfo(cfg.timezone))
            end_local = high.astimezone(ZoneInfo(cfg.timezone))
            day = local.date()
            start_day = date.fromisoformat(cfg.calendar.start)
            shift_lo = datetime.combine(
                day, time(cfg.calendar.shift_start), ZoneInfo(cfg.timezone)
            ).astimezone(UTC)
            shift_hi = (
                datetime.combine(day, time(cfg.calendar.shift_start), ZoneInfo(cfg.timezone))
                + timedelta(hours=cfg.calendar.shift_hours)
            ).astimezone(UTC)
            if (
                not (start_day <= day < start_day + timedelta(days=cfg.calendar.days))
                or day.weekday() not in cfg.calendar.weekdays
                or day.isoformat() in r.outages
                or low < shift_lo
                or high > shift_hi
            ):
                errors.append(f"{b.id}: outside work calendar")
            if a["destination"] != b.destination or (
                dest[b.destination].basis,
                dest[b.destination].material,
            ) != (b.basis, b.material):
                errors.append(f"{b.id}: destination/basis mismatch")
            if (
                a.get("material") != b.material
                or a.get("basis") != b.basis
                or a.get("ash") != b.ash
            ):
                errors.append(f"{b.id}: material provenance mismatch")
            by_block[b.id].append((low, high, q))
            by_resource[r.id].append((low, high, b.id))
            received[b.destination] += q
        except (KeyError, ValueError, TypeError):
            errors.append("Malformed allocation or unknown referenced object")
    for bid, items in by_block.items():
        b = blocks[bid]
        if not close(sum(x[2] for x in items), b.tonnes):
            errors.append(f"{bid}: quantity conservation mismatch")
        first = min(x[0] for x in items)
        for pred in b.predecessors:
            if pred not in by_block or max(x[1] for x in by_block[pred]) > first:
                errors.append(f"{bid}: precedence violated by {pred}")
        lock = locked_time(b, cfg)
        if lock and first != lock:
            errors.append(f"{bid}: date lock violated")
        ordered = sorted(items)
        if any(a[1] > b[0] for a, b in zip(ordered, ordered[1:])):
            errors.append(f"{bid}: concurrent split segments")
    for rid, items in by_resource.items():
        ordered = sorted(items)
        if any(a[1] > b[0] for a, b in zip(ordered, ordered[1:])):
            errors.append(f"{rid}: overlapping resource allocations")
    for did, d in dest.items():
        if d.opening + received[did] > d.capacity + 1e-4:
            errors.append(f"{did}: destination capacity exceeded")
    if result.get("status") == "feasible" and set(by_block) != set(blocks):
        errors.append("Feasible run contains unscheduled activities")
    for stock in result.get("stocks", []):
        d = dest.get(stock["id"])
        if not d or not close(stock["closing"], d.opening + received[d.id]):
            errors.append("Stock ledger mismatch")
    reported_stocks = result.get("stocks", [])
    if {s.get("id") for s in reported_stocks} != set(dest) or len(reported_stocks) != len(dest):
        errors.append("Missing or duplicate stock records")
    for stock in reported_stocks:
        d = dest.get(stock.get("id"))
        if not d:
            continue
        expected = d.opening + received[d.id]
        if stock.get("material") != d.material or stock.get("basis") != d.basis:
            errors.append(f"{d.id}: stock basis mismatch")
        if (
            not close(stock.get("opening", -1), d.opening)
            or not close(stock.get("receipts", -1), received[d.id])
            or stock.get("reclaim") != 0
            or stock.get("loss") != 0
        ):
            errors.append(f"{d.id}: stock ledger components mismatch")
        mass_ash = sum(
            a["tonnes"] * (a.get("ash") or 0)
            for a in result.get("allocations", [])
            if a.get("destination") == d.id
        ) + d.opening * (d.opening_ash or 0)
        quality = mass_ash / expected if expected and d.material == "coal" else None
        if (quality is None and stock.get("ash") is not None) or (
            quality is not None and (stock.get("ash") is None or not close(stock["ash"], quality))
        ):
            errors.append(f"{d.id}: weighted quality mismatch")
    period_expected = defaultdict(lambda: {"coal": 0.0, "waste": 0.0})
    for a in result.get("allocations", []):
        day = instant(a["start"]).astimezone(ZoneInfo(cfg.timezone)).date().isoformat()
        period_expected[day][a["material"]] += a["tonnes"]
    reported_periods = result.get("periods", [])
    if len(reported_periods) != len(period_expected):
        errors.append("Period ledger missing or duplicated")
    for p in reported_periods:
        if p.get("date") not in period_expected or any(
            not close(p.get(m, -1), period_expected[p["date"]][m]) for m in ["coal", "waste"]
        ):
            errors.append("Period production mismatch")
    totals = result.get("totals", {})
    for key, expected in [
        ("tonnes", sum(x[2] for items in by_block.values() for x in items)),
        (
            "coal",
            sum(
                x[2]
                for bid, items in by_block.items()
                if blocks[bid].material == "coal"
                for x in items
            ),
        ),
        (
            "waste",
            sum(
                x[2]
                for bid, items in by_block.items()
                if blocks[bid].material == "waste"
                for x in items
            ),
        ),
        ("volume", sum(blocks[bid].volume for bid in by_block)),
    ]:
        if key in totals and not close(totals[key], expected):
            errors.append(f"{key}: result total mismatch")
    return list(dict.fromkeys(errors))
