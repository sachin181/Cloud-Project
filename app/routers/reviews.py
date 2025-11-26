from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from ..services.db import get_session
from ..services.auth import get_current_user
from ..models.user import User
from ..services.sentiment import analyze_sentiment
from ..models.review import Review, ReviewCreate, ReviewRead, ReviewUpdate

router = APIRouter(prefix="/reviews", tags=["reviews"])

@router.post("", response_model=ReviewRead, status_code=201)
def create_review(
    payload: ReviewCreate,
    session: Session = Depends(get_session),
    user: User=Depends(get_current_user),
):
    # Enforce: one review per user per movie
    existing = session.exec(
        select(Review).where(
            Review.movie_id == payload.movie_id,
            Review.user_id == user.id,
        )
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="You already reviewed this movie")

    sentiment = analyze_sentiment(payload.body)

    review = Review(
        movie_id=payload.movie_id,
        user_id=user.id,
        rating=payload.rating,
        body=payload.body,
        sentiment_label=sentiment.label,
        sentiment_score=sentiment.score,
    )
    session.add(review)
    session.commit()
    session.refresh(review)
    return review

@router.get("", response_model=List[ReviewRead])
def list_reviews(
    movie_id: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
):
    stmt = select(Review)
    if movie_id:
        stmt = stmt.where(Review.movie_id == movie_id)
    results = session.exec(stmt.order_by(Review.created_at.desc())).all()
    return results

@router.get("/{review_id}", response_model=ReviewRead)
def get_review(review_id: int, session: Session = Depends(get_session)):
    review = session.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review

@router.patch("/{review_id}", response_model=ReviewRead)
def update_review(
    review_id: int,
    payload: ReviewUpdate,
    session: Session = Depends(get_session),
    user=Depends(get_current_user),
):
    review = session.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if str(review.user_id) != str(user.id):
        raise HTTPException(status_code=403, detail="Not your review")

    if payload.rating is not None:
        review.rating = payload.rating
    if payload.body is not None:
        review.body = payload.body
        sentiment = analyze_sentiment(payload.body)
        review.sentiment_label = sentiment.label
        review.sentiment_score = sentiment.score

    session.add(review)
    session.commit()
    session.refresh(review)
    return review

@router.delete("/{review_id}", status_code=204)
def delete_review(
    review_id: int,
    session: Session = Depends(get_session),
    user=Depends(get_current_user),
):
    review = session.get(Review, review_id)
    if not review:
        return
    if str(review.user_id) != str(user.id):
        raise HTTPException(status_code=403, detail="Not your review")
    session.delete(review)
    session.commit()
