from fastapi import FastAPI
from .config import settings
from .services.db import init_db

from .routers import health, movies, reviews, auth

app = FastAPI(title=settings.app_name, version=settings.version)

# Initialize Firebase/Firestore
init_db()

app.include_router(health.router)
app.include_router(movies.router)
app.include_router(auth.router)
app.include_router(reviews.router)

@app.get("/")
def root():
    return {"message": "Welcome to the Movie Review Backend. See /docs for interactive docs."}
