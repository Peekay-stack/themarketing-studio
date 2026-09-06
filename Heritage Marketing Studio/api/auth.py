"""auth.py — password hashing and session tokens, stdlib only.

Round 46: the login contract Design needs before building the sign-in screen. PBKDF2-HMAC-SHA256 via
hashlib rather than a bcrypt/passlib dependency — one fewer thing that can fail to install on a
Windows dev box that has already had setup friction, and PBKDF2 at a real iteration count is a
legitimate, still-recommended construction (it's Django's own default).

Sessions are server-side rows, not stateless tokens: logout deletes the row, so a leaked token stops
working the moment someone signs out, which a bare "forget it client-side" logout cannot promise.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import os
import secrets

PBKDF2_ITERATIONS = 260_000
SESSION_BYTES = 32
SESSION_LIFETIME = dt.timedelta(days=14)


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt),
                                  PBKDF2_ITERATIONS).hex()
    return f"{salt}${PBKDF2_ITERATIONS}${digest}"


def verify_password(password: str, stored: str) -> bool:
    if not stored or stored.count("$") != 2:
        return False
    salt, iterations, digest = stored.split("$")
    check = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt),
                                 int(iterations)).hex()
    return hmac.compare_digest(check, digest)


def new_session_token() -> str:
    return secrets.token_urlsafe(SESSION_BYTES)


def utcnow() -> dt.datetime:
    """Naive UTC, deliberately -- SQLite's DateTime column round-trips as naive regardless of what
    goes in, so comparing a stored `expires` against an aware `now()` raises TypeError. Every session
    timestamp in this module goes through this one function so storage and comparison always agree."""
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)


def session_expiry(now: dt.datetime | None = None) -> dt.datetime:
    return (now or utcnow()) + SESSION_LIFETIME


COOKIE_NAME = "studio_session"

# Cookies are Secure by default (HTTPS-only) -- turned off only for plain-http local dev, where a
# Secure cookie would silently never be sent and login would look broken with no error to explain
# why. STUDIO_INSECURE_COOKIES=1 opts into that for local http:// testing; unset (or 0) in anything
# that isn't localhost.
COOKIE_SECURE = os.environ.get("STUDIO_INSECURE_COOKIES", "0") != "1"
