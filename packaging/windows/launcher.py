"""Self-contained local Windows launcher; no system Python, Node or Docker."""

from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import socket
import sys
import threading
import time
import webbrowser


def data_directory():
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "MESSI"
    return Path.home() / ".local" / "share" / "MESSI"


def choose_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--login-details", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    data = (args.data_dir or data_directory()).resolve()
    data.mkdir(parents=True, exist_ok=True, mode=0o700)
    # One instance per local data directory. Closing the console releases the OS lock.
    lock = (data / "application.lock").open("a+b")
    lock.seek(0)
    lock.write(b"0")
    lock.flush()
    lock.seek(0)
    try:
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        if args.login_details and os.name == "nt":
            os.startfile(str(data / "LOGIN-DETAILS.txt"))
            return
        try:
            instance = json.loads((data / "instance.json").read_text())
            port = int(instance["port"])
            if 1024 <= port <= 65535 and not args.no_browser:
                webbrowser.open(f"http://127.0.0.1:{port}")
        except (OSError, ValueError, KeyError):
            pass
        print("MESSI is already running. Use its existing window.")
        return
    port = args.port or choose_port()
    origin = f"http://127.0.0.1:{port}"
    os.environ["MESSI_DATA_DIR"] = str(data)
    os.environ["DATABASE_URL"] = "sqlite:///" + (data / "messi.db").as_posix()
    os.environ["MESSI_ORIGINS"] = origin
    os.environ["MESSI_SECURE_COOKIES"] = "0"  # Loopback-only HTTP, never public hosting.
    sys.path.insert(0, str(root / "backend"))
    from messi.bootstrap import bootstrap

    bootstrap()
    details = data / "LOGIN-DETAILS.txt"
    if not details.exists() and (data / "bootstrap-users.json").exists():
        accounts = json.loads((data / "bootstrap-users.json").read_text())
        owner = next(x for x in accounts if x["role"] == "owner")
        fd = os.open(details, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "w") as out:
            out.write(
                "MESSI PRIVATE LOGIN DETAILS\n\nEmail: "
                + owner["email"]
                + "\nPassword: "
                + owner["password"]
                + "\n\nKeep this file private. Data is stored in this folder; do not delete it.\n"
            )
        if os.name == "nt" and not args.no_browser:
            os.startfile(str(details))
    if args.login_details:
        if os.name == "nt":
            os.startfile(str(details))
        return
    from messi.api import app
    from messi.worker import process_once
    import uvicorn

    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, access_log=False, log_level="warning")
    )
    stop = threading.Event()

    def work():
        while not stop.is_set():
            try:
                if not process_once():
                    stop.wait(0.5)
            except Exception:
                print("Planning worker stopped. Restart MESSI; your saved data is retained.")
                server.should_exit = True
                break

    worker = threading.Thread(target=work, daemon=True, name="MESSI-local-worker")
    worker.start()
    (data / "instance.json").write_text(json.dumps({"port": port, "pid": os.getpid()}))

    def open_when_ready():
        for _ in range(200):
            if server.started:
                if not args.no_browser:
                    webbrowser.open(origin)
                return
            if stop.wait(0.1):
                return

    threading.Thread(target=open_when_ready, daemon=True).start()
    print("MESSI is starting in your browser. Keep this window open.")
    print("Private data folder:", data)
    print("Local address:", origin)
    try:
        server.run()
    finally:
        stop.set()
        worker.join(timeout=5)
        lock.close()


if __name__ == "__main__":
    main()
