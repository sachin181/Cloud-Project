import json
import os
from typing import Optional
import firebase_admin
from firebase_admin import credentials, firestore
from ..config import settings

# Global Firestore client
db: Optional[firestore.Client] = None


def init_db():
    """
    Initialize Firebase Admin SDK and Firestore client.
    
    Supports two methods:
    1. FIREBASE_CREDENTIALS_PATH - path to service account JSON file
    2. FIREBASE_CREDENTIALS_JSON - JSON string with credentials
    """
    global db
    
    # Skip if already initialized
    if db is not None:
        return
    
    # Check if Firebase is already initialized
    try:
        firebase_admin.get_app()
        db = firestore.client()
        return
    except ValueError:
        # Not initialized yet, continue
        pass
    
    # Initialize Firebase Admin SDK
    cred = None
    
    if settings.firebase_credentials_path:
        # Method 1: Load from file path
        if os.path.exists(settings.firebase_credentials_path):
            cred = credentials.Certificate(settings.firebase_credentials_path)
        else:
            raise FileNotFoundError(
                f"Firebase credentials file not found: {settings.firebase_credentials_path}"
            )
    elif settings.firebase_credentials_json:
        # Method 2: Load from JSON string
        try:
            cred_dict = json.loads(settings.firebase_credentials_json)
            cred = credentials.Certificate(cred_dict)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid Firebase credentials JSON: {e}")
    else:
        # Try to use default credentials (for local development with gcloud)
        try:
            cred = credentials.ApplicationDefault()
        except Exception:
            raise ValueError(
                "Firebase credentials not configured. Set FIREBASE_CREDENTIALS_PATH "
                "or FIREBASE_CREDENTIALS_JSON environment variable."
            )
    
    firebase_admin.initialize_app(cred)
    db = firestore.client()


def get_db() -> firestore.Client:
    """
    Get the Firestore client instance.
    Initializes Firebase if not already initialized.
    """
    if db is None:
        init_db()
    return db
