"""Exercise the extracted application without relying on an installed server.
Pass --native on Windows to run its actual bundled python.exe.
"""

import argparse, json, os, socket, subprocess, sys, tempfile, time
from pathlib import Path
import urllib.request

p = argparse.ArgumentParser()
p.add_argument("package", type=Path)
p.add_argument("--native", action="store_true")
args = p.parse_args()
package = args.package.resolve()
python = package / "runtime" / "python.exe" if args.native else Path(sys.executable)
with tempfile.TemporaryDirectory(prefix="MESSI-portable-test-") as folder:
    data = Path(folder)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    proc = subprocess.Popen(
        [
            str(python),
            "-I",
            str(package / "app" / "launcher.py"),
            "--no-browser",
            "--data-dir",
            str(data),
            "--port",
            str(port),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    try:
        for _ in range(200):
            try:
                with urllib.request.urlopen(url + "/api/health", timeout=1) as r:
                    assert r.status == 200
                break
            except Exception:
                if proc.poll() is not None:
                    raise RuntimeError("Portable launcher exited before readiness")
                time.sleep(0.1)
        else:
            raise RuntimeError("Portable startup timed out")
        env = {
            **os.environ,
            "MESSI_SMOKE_URL": url,
            "MESSI_ACCOUNTS_FILE": str(data / "bootstrap-users.json"),
        }
        subprocess.run([str(python), "-I", str(package / "app" / "smoke.py")], env=env, check=True)
        assert (data / "LOGIN-DETAILS.txt").exists()
        with urllib.request.urlopen(url) as r:
            assert b'<div id="root"' in r.read()
        # A second launch must not start another worker/server on the same data.
        second = subprocess.run(
            [
                str(python),
                "-I",
                str(package / "app" / "launcher.py"),
                "--no-browser",
                "--data-dir",
                str(data),
            ],
            capture_output=True,
            timeout=15,
        )
        assert second.returncode == 0 and b"already running" in second.stdout
        print(
            "Portable app: functional schedule/export, bundled SPA, login file and single-instance guard passed."
        )
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
