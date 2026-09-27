from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.models.database import User
from backend.models.schemas import UserCreate

password_hash = PasswordHash.recommended()
DUMMY_HASH = password_hash.hash("unused-password-for-timing")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(user_id: int, expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    duration = (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    return jwt.encode(
        {"sub": str(user_id), "iat": now, "exp": now + duration},
        settings.secret_key.get_secret_value(),
        algorithm="HS256",
    )


def decode_token(token: str) -> int | None:
    try:
        payload = jwt.decode(
            token,
            get_settings().secret_key.get_secret_value(),
            algorithms=["HS256"],
            options={"require": ["sub", "iat", "exp"]},
        )
        user_id = int(payload["sub"])
        return user_id if user_id > 0 else None
    except (jwt.InvalidTokenError, ValueError, TypeError):
        return None


def create_user(db: Session, user_create: UserCreate) -> User:
    user = User(
        email=str(user_create.email).lower(),
        username=user_create.username,
        password_hash=hash_password(user_create.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("Email or username is already registered") from exc
    db.refresh(user)
    return user


def authenticate_user(db: Session, identifier: str, password: str) -> User | None:
    user = db.scalar(
        select(User).where(or_(User.email == identifier.lower(), User.username == identifier))
    )
    valid = verify_password(password, user.password_hash if user else DUMMY_HASH)
    return user if valid else None
