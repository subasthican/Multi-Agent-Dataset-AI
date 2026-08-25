import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .db import get_db
from .db_models import User
from .jwt_manager import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed_password.encode())


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email.lower()).first()


def register_user(db: Session, name: str, email: str, password: str) -> User:
    if get_user_by_email(db, email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(name=name, email=email.lower(), hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        # Distinct from a bad password on purpose — the credentials are
        # correct, access is what's denied, and the frontend shows this
        # detail directly rather than a generic "invalid login" message.
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account has been suspended.")
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    if credentials is None:
        raise unauthorized

    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.PyJWTError:
        raise unauthorized

    user = db.get(User, payload.get("sub"))
    if user is None or not user.is_active:
        # A suspended user's existing token stops working immediately, the
        # same way is_admin is re-checked from the DB every request rather
        # than trusted from the token — not just blocked at the next login.
        raise unauthorized
    return user


def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Same as get_current_user, plus an admin check. Layered on top of
    get_current_user rather than duplicating its logic - an invalid/missing
    token still 401s before this ever checks is_admin."""
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """Same as get_current_user, but returns None instead of raising when
    there's no/invalid token — for endpoints (like /discover) that must stay
    usable without an account, but behave differently when one is present."""
    if credentials is None:
        return None
    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.PyJWTError:
        return None
    user = db.get(User, payload.get("sub"))
    if user is not None and not user.is_active:
        # Treated the same as "no token" rather than raising — callers of
        # this dependency (e.g. /discover) must stay usable without an
        # account, and a suspended user degrading to anonymous behavior
        # (subject to the same IP-tracked Free limit) is more consistent
        # than a hard failure here.
        return None
    return user
