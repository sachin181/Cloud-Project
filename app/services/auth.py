# app/services/auth.py

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import Session, select

from ..config import settings
from ..services.db import get_session
from ..models.user import User

# OAuth2 bearer token – Swagger will use /auth/login to get tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Use pbkdf2_sha256 (no bcrypt issues on Windows)
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


# ---------- Password helpers ---------- #

def hash_password(password: str) -> str:
    """Hash a plain password for storage."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain, hashed)


# ---------- DB helper ---------- #

def get_user_by_email(email: str, session: Session) -> Optional[User]:
    """Find a user by email, or return None."""
    return session.exec(select(User).where(User.email == email)).first()


# ---------- JWT helpers ---------- #

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed JWT access token.

    `data` should already contain e.g. {"sub": "<user_id>"} as strings.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta
        if expires_delta
        else timedelta(minutes=settings.jwt_access_token_expires_minutes)
    )
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt


# ---------- Dependency used in protected endpoints ---------- #

def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> User:
    """
    Resolve the current authenticated user from the Bearer token.
    Raises 401 if token invalid or user not found.
    """
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode token
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        sub = payload.get("sub")
        if sub is None:
            raise cred_exc

        # Accept sub as string or int
        try:
            user_id = int(sub)
        except (TypeError, ValueError):
            raise cred_exc

    except JWTError:
        raise cred_exc

    # Look up user in DB
    user = session.get(User, user_id)
    if not user:
        raise cred_exc

    return user
