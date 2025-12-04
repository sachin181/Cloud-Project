import os
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()

class Settings(BaseModel):
    app_name: str = "Movie Review Backend"
    version: str = "1.0.0"
    env: str = os.environ.get("ENV", "dev")

    # Firebase configuration
    # Path to Firebase service account JSON file
    firebase_credentials_path: str = os.environ.get("FIREBASE_CREDENTIALS_PATH", "")
    # Or use JSON string directly (useful for deployment)
    firebase_credentials_json: str = os.environ.get("FIREBASE_CREDENTIALS_JSON", "")

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
