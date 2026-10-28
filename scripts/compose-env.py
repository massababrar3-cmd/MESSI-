from pathlib import Path
import secrets, os

root = Path(__file__).resolve().parents[1]
p = root / ".local/compose.env"
p.parent.mkdir(exist_ok=True, mode=0o700)
fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, "w") as f:
    f.write("DB_PASSWORD=" + secrets.token_hex(24) + "\n")
print("Private compose environment created. Existing values are never overwritten.")
