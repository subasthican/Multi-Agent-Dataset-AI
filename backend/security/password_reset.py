import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from .authentication import hash_password
from .db_models import PasswordResetToken, User

RESET_TOKEN_EXPIRY_MINUTES = 30


def create_reset_token(db: Session, user: User) -> str:
    token = secrets.token_urlsafe(32)
    reset_token = PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_EXPIRY_MINUTES),
    )
    db.add(reset_token)
    db.commit()
    return token


def consume_reset_token(db: Session, token: str, new_password: str) -> bool:
    record = db.query(PasswordResetToken).filter(PasswordResetToken.token == token).first()
    if not record or record.used:
        return False

    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return False

    user = db.get(User, record.user_id)
    if user is None:
        return False

    user.hashed_password = hash_password(new_password)
    record.used = True
    db.commit()
    return True
