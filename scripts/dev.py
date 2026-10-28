"""Launch API + durable worker + Vite (or serve built SPA). No credentials logged."""

import os, sys, signal, subprocess, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
python = str(ROOT / ".venv/bin/python") if (ROOT / ".venv/bin/python").exists() else sys.executable
env = {**os.environ, "PYTHONPATH": str(ROOT / "backend")}
subprocess.run([python, "-m", "messi.bootstrap"], env=env, check=True)
production = "--production" in sys.argv
commands = [
    [
        python,
        "-m",
        "uvicorn",
        "messi.api:app",
        "--no-access-log",
        "--host",
        os.environ.get("API_HOST", "127.0.0.1"),
        "--port",
        os.environ.get("API_PORT", "8000"),
    ],
    [python, "-m", "messi.worker"],
]
if not production:
    commands.append(["npm", "run", "dev", "--workspace", "frontend"])
children = []


def stop(*_):
    for p in children:
        if p.poll() is None:
            try:
                os.killpg(p.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
    for p in children:
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass


signal.signal(signal.SIGINT, stop)
signal.signal(signal.SIGTERM, stop)
try:
    children = [subprocess.Popen(cmd, env=env, start_new_session=True) for cmd in commands]
    while all(p.poll() is None for p in children):
        time.sleep(0.5)
finally:
    stop()
