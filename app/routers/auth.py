# app/routers/auth.py

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from firebase_admin import auth
from firebase_admin.exceptions import FirebaseError

from ..models.user import UserRead
from ..services.auth import get_current_user, get_user_id
from ..services.db import get_db
from google.cloud.firestore import Client as FirestoreClient

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserRead)
def me(
    current_user: dict = Depends(get_current_user),
    db: FirestoreClient = Depends(get_db),
):
    """
    Return the currently authenticated user.
    
    If the user doesn't exist in Firestore, create a user document.
    The user is authenticated via Firebase ID token.
    """
    uid = current_user.get("uid")
    email = current_user.get("email", "")
    
    if not uid:
        raise HTTPException(status_code=401, detail="Invalid token: missing uid")
    
    # Check if user exists in Firestore, if not create it
    user_ref = db.collection("users").document(uid)
    user_doc = user_ref.get()
    
    if not user_doc.exists:
        # Create user document in Firestore
        user_data = {
            "uid": uid,
            "email": email,
            "created_at": datetime.utcnow(),
        }
        user_ref.set(user_data)
        return UserRead(**user_data)
    
    # Return existing user
    user_data = user_doc.to_dict()
    return UserRead(**user_data)
