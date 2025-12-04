# app/routers/movies.py

from typing import Optional, List, Dict, Any

import requests
from fastapi import APIRouter, HTTPException, Query, Depends
from google.cloud.firestore import Client as FirestoreClient

from ..services.db import get_db

router = APIRouter(prefix="/movies", tags=["movies"])

# Public demo API (Studio Ghibli)
GHIBLI_FILMS_URL = "https://ghibliapi.vercel.app/films"


def _fetch_all_movies() -> List[Dict[str, Any]]:
    resp = requests.get(GHIBLI_FILMS_URL, timeout=10)
    resp.raise_for_status()
    movies: List[Dict[str, Any]] = resp.json()

    # Normalize a few fields we care about
    for m in movies:
        m.setdefault("release_date", None)
        m.setdefault("rt_score", "0")
        m.setdefault("running_time", None)
    return movies


# -------------------------
# Basic movie catalogue API
# -------------------------


@router.get("")
def list_movies(
    q: Optional[str] = Query(
        None, description="Full-text search on title/original title/description"
    ),
    year: Optional[int] = Query(
        None, description="Filter by release year (e.g. 2001)"
    ),
    sort: Optional[str] = Query(
        "title:asc",
        description='Sort by "title|year|score" with :asc or :desc (e.g. score:desc)',
    ),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
):
    """
    List movies from the public Studio Ghibli API.

    Example:
      /movies?q=castle&year=2004&sort=score:desc&page=1&limit=5
    """
    movies = _fetch_all_movies()

    # Filter: text search
    if q:
        q_lower = q.lower()
        movies = [
            m
            for m in movies
            if q_lower in (m.get("title") or "").lower()
            or q_lower in (m.get("original_title") or "").lower()
            or q_lower in (m.get("description") or "").lower()
        ]

    # Filter: year
    if year is not None:
        movies = [m for m in movies if str(year) == str(m.get("release_date"))]

    # Sort
    key, _, direction = (sort + ":asc").partition(":")
    key = key.lower()
    reverse = direction.lower() == "desc"

    def sort_key(m: Dict[str, Any]):
        if key == "title":
            return (m.get("title") or "").lower()
        if key == "year":
            try:
                return int(m.get("release_date") or 0)
            except ValueError:
                return 0
        if key in ("score", "rating"):
            try:
                return int(m.get("rt_score") or 0)
            except ValueError:
                return 0
        # default
        return (m.get("title") or "").lower()

    movies.sort(key=sort_key, reverse=reverse)

    # Pagination
    total = len(movies)
    start = (page - 1) * limit
    end = start + limit
    items = movies[start:end]

    def expose(m: Dict[str, Any]):
        return {
            "id": m.get("id"),
            "title": m.get("title"),
            "year": m.get("release_date"),
            "runtime": m.get("running_time"),
            "posterUrl": m.get("image"),
            "synopsis": m.get("description"),
            "score": m.get("rt_score"),
            "director": m.get("director"),
        }

    base = "/movies"
    next_link = None
    if end < total:
        next_link = (
            f"{base}?q={q or ''}&year={year or ''}&sort={sort}&page={page+1}&limit={limit}"
        )

    return {
        "items": [expose(m) for m in items],
        "page": page,
        "limit": limit,
        "total": total,
        "next": next_link,
    }


@router.get("/{movie_id}")
def get_movie(movie_id: str):
    """
    Get detailed information about a single movie from the Ghibli API.
    """
    movies = _fetch_all_movies()
    for m in movies:
        if m.get("id") == movie_id:
            return {
                "id": m.get("id"),
                "title": m.get("title"),
                "original_title": m.get("original_title"),
                "year": m.get("release_date"),
                "runtime": m.get("running_time"),
                "posterUrl": m.get("image"),
                "bannerUrl": m.get("movie_banner"),
                "synopsis": m.get("description"),
                "score": m.get("rt_score"),
                "director": m.get("director"),
                "producer": m.get("producer"),
                "url": m.get("url"),
            }
    raise HTTPException(status_code=404, detail="Movie not found")


# --------------------------------
# NEW: Overall sentiment endpoint
# --------------------------------


@router.get("/{movie_id}/sentiment")
def get_movie_sentiment(
    movie_id: str,
    db: FirestoreClient = Depends(get_db),
):
    """
    Compute overall sentiment for a movie based on all stored reviews.

    Returns:
      - review_count
      - average_rating  (1–5)
      - overall_sentiment  ("positive" | "neutral" | "negative" | null)
      - sentiment_score (average of scores, -1..1, or null)
    """
    # Query reviews for this movie from Firestore
    reviews_query = (
        db.collection("reviews")
        .where("movie_id", "==", movie_id)
        .get()
    )
    
    reviews = [doc.to_dict() for doc in reviews_query]

    if not reviews:
        return {
            "movie_id": movie_id,
            "review_count": 0,
            "average_rating": None,
            "overall_sentiment": None,
            "sentiment_score": None,
        }

    # Average numeric rating
    avg_rating = sum(r.get("rating", 0) for r in reviews) / len(reviews)

    # Average sentiment score (only where present)
    scores = [
        r.get("sentiment_score")
        for r in reviews
        if r.get("sentiment_score") is not None
    ]
    avg_sent_score: Optional[float] = (
        sum(scores) / len(scores) if scores else None
    )

    # Derive overall label from the average score
    if avg_sent_score is None:
        overall_label = None
    else:
        if avg_sent_score > 0.2:
            overall_label = "positive"
        elif avg_sent_score < -0.2:
            overall_label = "negative"
        else:
            overall_label = "neutral"

    return {
        "movie_id": movie_id,
        "review_count": len(reviews),
        "average_rating": avg_rating,
        "overall_sentiment": overall_label,
        "sentiment_score": avg_sent_score,
    }

