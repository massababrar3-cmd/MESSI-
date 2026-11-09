"""Cross-package official CPython NuGet + hash-locked Windows wheels + built SPA.

No Windows binaries are executed by this cross-build. Native smoke testing is
provided separately through the Windows CI workflow.
"""

import base64, hashlib, json, os, shutil, subprocess, sys, urllib.request, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / ".local" / "windows-build"
OUT = ROOT / ".local" / "windows-portable"
PYTHON = "3.13.17"
TZDATA = "2026.6"
COLORAMA = "0.4.6"


def fetch(url):
    with urllib.request.urlopen(url, timeout=90) as response:
        return response.read()


def safe_extract(z, target, prefix=""):
    for item in z.infolist():
        if prefix and not item.filename.startswith(prefix):
            continue
        name = item.filename[len(prefix) :]
        if not name:
            continue
        dest = (target / name).resolve()
        if not dest.is_relative_to(target.resolve()):
            raise ValueError("Unsafe archive path")
        if item.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(z.read(item))


def build():
    CACHE.mkdir(parents=True, exist_ok=True)
    registration = json.loads(
        fetch(f"https://api.nuget.org/v3/registration5-semver1/python/{PYTHON}.json")
    )
    catalog = json.loads(fetch(registration["catalogEntry"]))
    if catalog["packageHashAlgorithm"] != "SHA512":
        raise ValueError("Unexpected runtime hash algorithm")
    archive = CACHE / f"python-{PYTHON}.nupkg"
    if not archive.exists():
        archive.write_bytes(fetch(registration["packageContent"]))
    if (
        base64.b64encode(hashlib.sha512(archive.read_bytes()).digest()).decode()
        != catalog["packageHash"]
    ):
        raise ValueError("Official CPython archive checksum mismatch")
    if OUT.exists():
        shutil.rmtree(OUT)
    package = OUT / "MESSI-Windows"
    runtime = package / "runtime"
    app = package / "app"
    runtime.mkdir(parents=True)
    app.mkdir()
    with zipfile.ZipFile(archive) as z:
        safe_extract(z, runtime, "tools/")
    tz = json.loads(fetch(f"https://pypi.org/pypi/tzdata/{TZDATA}/json"))
    tz_wheel = next(f for f in tz["urls"] if f["filename"].endswith(".whl"))
    lock = CACHE / "windows-requirements.txt"
    color = json.loads(fetch(f"https://pypi.org/pypi/colorama/{COLORAMA}/json"))
    color_wheel = next(f for f in color["urls"] if f["filename"].endswith(".whl"))
    lock.write_text(
        (ROOT / "backend/requirements.txt").read_text()
        + f"\ntzdata=={TZDATA} --hash=sha256:{tz_wheel['digests']['sha256']}\ncolorama=={COLORAMA} --hash=sha256:{color_wheel['digests']['sha256']}\n"
    )
    wheels = CACHE / "wheels"
    if wheels.exists():
        shutil.rmtree(wheels)
    wheels.mkdir()
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "download",
            "--disable-pip-version-check",
            "--require-hashes",
            "--only-binary=:all:",
            "--platform",
            "win_amd64",
            "--implementation",
            "cp",
            "--python-version",
            "3.13",
            "--abi",
            "cp313",
            "--dest",
            str(wheels),
            "-r",
            str(lock),
        ],
        check=True,
    )
    site = runtime / "Lib" / "site-packages"
    site.mkdir(parents=True, exist_ok=True)
    for wheel in wheels.glob("*.whl"):
        with zipfile.ZipFile(wheel) as z:
            safe_extract(z, site)
            # Wheel .data/purelib and platlib must be relocated per the wheel spec.
            for data in site.glob("*.data"):
                for kind in ["purelib", "platlib"]:
                    if (data / kind).exists():
                        shutil.copytree(data / kind, site, dirs_exist_ok=True)
                        shutil.rmtree(data / kind)
    shutil.copytree(
        ROOT / "backend" / "messi",
        app / "backend" / "messi",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    shutil.copytree(ROOT / "frontend" / "dist", app / "frontend" / "dist")
    shutil.copy(ROOT / "packaging/windows/launcher.py", app / "launcher.py")
    shutil.copy(ROOT / "scripts/smoke.py", app / "smoke.py")
    for name in ["START-MESSI.cmd", "SHOW-LOGIN.cmd", "READ-ME-FIRST.txt"]:
        text = (ROOT / "packaging/windows" / name).read_text()
        (package / name).write_bytes(text.replace("\n", "\r\n").encode())
    shutil.copytree(ROOT / "docs", package / "documentation")
    manifest = {
        "python_version": PYTHON,
        "python_source": registration["packageContent"],
        "python_catalog": registration["catalogEntry"],
        "python_sha512": catalog["packageHash"],
        "tzdata_version": TZDATA,
        "wheels": {
            f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in wheels.glob("*.whl")
        },
        "native_windows_test": "Not executed by the cross-build; see CI results separately.",
    }
    (package / "BUILD-MANIFEST.json").write_text(json.dumps(manifest, indent=2))
    target = Path(
        os.environ.get(
            "MESSI_WINDOWS_ZIP", str(ROOT.parent / "scratch" / "MESSI-Windows-Portable.zip")
        )
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for f in sorted(package.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(OUT))
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    target.with_suffix(".zip.sha256").write_text(digest + "  " + target.name + "\n")
    print("Windows portable package:", target, "bytes:", target.stat().st_size, "sha256:", digest)


if __name__ == "__main__":
    build()
