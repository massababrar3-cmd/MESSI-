import hashlib, hmac, secrets, time
from fastapi import HTTPException, Request
from sqlalchemy import select
from .db import LoginSession, User


def hash_password(value):
    if len(value) < 12:
        raise ValueError("Use a password of at least 12 characters")
    salt = secrets.token_hex(16)
    digest = hashlib.scrypt(value.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()
    return f"scrypt${salt}${digest}"


def verify_password(value, stored):
    try:
        _, salt, digest = stored.split("$")
        actual = hashlib.scrypt(value.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()
        return hmac.compare_digest(actual, digest)
    except (ValueError, TypeError):
        return False


def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def identity(db, request: Request, mutation=False):
    token = request.cookies.get("messi_session", "")
    s = db.get(LoginSession, digest(token))
    if not s or s.expires < time.time():
        raise HTTPException(401, "Sign in to continue")
    if mutation and not hmac.compare_digest(request.headers.get("x-csrf-token", ""), s.csrf):
        raise HTTPException(403, "CSRF token missing or invalid")
    user = db.get(User, s.user_id)
    if not user:
        raise HTTPException(401, "Session is no longer valid")
    return user, s
