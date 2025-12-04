from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from google.cloud.firestore import Client as FirestoreClient

from ..services.db import get_db
from ..services.auth import get_current_user, get_user_id
from ..services.sentiment import analyze_sentiment
from ..models.review import Review, ReviewCreate, ReviewRead, ReviewUpdate

router = APIRouter(prefix="/reviews", tags=["reviews"])


def _review_to_dict(review_doc) -> dict:
    """Convert Firestore document to dict for ReviewRead."""
    data = review_doc.to_dict()
    data["id"] = review_doc.id
    return data


@router.post("", response_model=ReviewRead, status_code=201)
def create_review(
    payload: ReviewCreate,
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a new review. Enforces one review per user per movie."""
    user_id = get_user_id(current_user)
    
    # Check if user already reviewed this movie
    existing_query = (
        db.collection("reviews")
        .where("movie_id", "==", payload.movie_id)
        .where("user_id", "==", user_id)
        .limit(1)
        .get()
    )
    
    if list(existing_query):
        raise HTTPException(
            status_code=409, detail="You already reviewed this movie"
        )
    
    # Analyze sentiment
    sentiment = analyze_sentiment(payload.body)
    
    # Create review document
    now = datetime.utcnow()
    review_data = {
        "movie_id": payload.movie_id,
        "user_id": user_id,
        "rating": payload.rating,
        "body": payload.body,
        "sentiment_label": sentiment.label,
        "sentiment_score": sentiment.score,
        "created_at": now,
        "updated_at": now,
    }
    
    # Add to Firestore
    doc_ref = db.collection("reviews").add(review_data)
    review_data["id"] = doc_ref.id
    
    return ReviewRead(**review_data)


@router.get("", response_model=List[ReviewRead])
def list_reviews(
    movie_id: Optional[str] = Query(default=None),
    db: FirestoreClient = Depends(get_db),
):
    """List reviews, optionally filtered by movie_id."""
    query = db.collection("reviews")
    
    if movie_id:
        query = query.where("movie_id", "==", movie_id)
    
    # Order by created_at descending
    reviews = query.order_by("created_at", direction="DESCENDING").get()
    
    return [ReviewRead(**_review_to_dict(doc)) for doc in reviews]


@router.get("/{review_id}", response_model=ReviewRead)
def get_review(
    review_id: str,
    db: FirestoreClient = Depends(get_db),
):
    """Get a single review by ID."""
    doc_ref = db.collection("reviews").document(review_id)
    doc = doc_ref.get()
    
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Review not found")
    
    return ReviewRead(**_review_to_dict(doc))


@router.patch("/{review_id}", response_model=ReviewRead)
def update_review(
    review_id: str,
    payload: ReviewUpdate,
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update a review. Only the owner can update their review."""
    user_id = get_user_id(current_user)
    
    doc_ref = db.collection("reviews").document(review_id)
    doc = doc_ref.get()
    
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Review not found")
    
    review_data = doc.to_dict()
    
    # Check ownership
    if review_data.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Not your review")
    
    # Update fields
    update_data = {"updated_at": datetime.utcnow()}
    
    if payload.rating is not None:
        update_data["rating"] = payload.rating
    
    if payload.body is not None:
        update_data["body"] = payload.body
        # Re-analyze sentiment if body changed
        sentiment = analyze_sentiment(payload.body)
        update_data["sentiment_label"] = sentiment.label
        update_data["sentiment_score"] = sentiment.score
    
    # Update in Firestore
    doc_ref.update(update_data)
    
    # Get updated document
    updated_doc = doc_ref.get()
    review_data = updated_doc.to_dict()
    review_data["id"] = updated_doc.id
    
    return ReviewRead(**review_data)


@router.delete("/{review_id}", status_code=204)
def delete_review(
    review_id: str,
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete a review. Only the owner can delete their review."""
    user_id = get_user_id(current_user)
    
    doc_ref = db.collection("reviews").document(review_id)
    doc = doc_ref.get()
    
    if not doc.exists:
        return
    
    review_data = doc.to_dict()
    
    # Check ownership
    if review_data.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Not your review")
    
    # Delete from Firestore
    doc_ref.delete()
