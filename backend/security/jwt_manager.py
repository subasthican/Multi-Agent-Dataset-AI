import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt

ALGORITHM = "HS256"
DEFAULT_EXPIRY_HOURS = 2

# Falls back to a random secret generated at process start when SECRET_KEY
# isn't set, so local dev works out of the box — tokens just won't survive a
# restart. Set SECRET_KEY in the repo-root .env for a persistent secret.
SECRET_KEY = os.getenv("JWT_SECRET_KEY") or secrets.token_hex(32)


def create_access_token(user_id: str, email: str) -> str:
    expires_hours = int(os.getenv("JWT_EXPIRY_HOURS", DEFAULT_EXPIRY_HOURS))
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=expires_hours),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
