import os
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()

class Settings(BaseModel):
    app_name: str = "Movie Review Backend"
    version: str = "1.0.0"
    env: str = os.environ.get("ENV", "dev")
    database_url: str = os.environ.get("DATABASE_URL", "sqlite:///./data.db")

    # JWT auth config
    jwt_secret_key: str = os.environ.get("JWT_SECRET_KEY", "dev-secret-change-me")
    jwt_algorithm: str = "HS256"
    jwt_access_token_expires_minutes: int = 60 * 24  # 1 day

    # Movies API
    ghibli_films_url: str = os.environ.get(
        "GHIBLI_FILMS_URL",
        "https://ghibliapi.vercel.app/films",
    )

    # Sentiment provider: "openai" or "mock"
    sentiment_provider: str = os.environ.get("SENTIMENT_PROVIDER", "openai")

    # OpenAI
    openai_api_key: str = os.environ.get("OPENAI_API_KEY", "")

settings = Settings()
