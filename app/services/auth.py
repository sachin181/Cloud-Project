# app/services/auth.py

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth
from firebase_admin.exceptions import FirebaseError

from ..services.db import init_db

# Initialize Firebase on import
init_db()

# HTTP Bearer token scheme
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Verify Firebase ID token and return the decoded token (user info).
    
    The token should be obtained from Firebase Auth on the client side.
    Raises 401 if token is invalid or expired.
    """
    token = credentials.credentials
    
    try:
        # Verify the ID token
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except ValueError:
        # Invalid token format
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except FirebaseError as e:
        # Token expired or invalid
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_user_id(current_user: dict = Depends(get_current_user)) -> str:
    """
    Extract user ID (uid) from the decoded Firebase token.
    """
    return current_user.get("uid")


def get_user_email(current_user: dict = Depends(get_current_user)) -> Optional[str]:
    """
    Extract user email from the decoded Firebase token.
    """
    return current_user.get("email")
