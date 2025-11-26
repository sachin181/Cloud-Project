from typing import List, Dict, Any
import requests
from ..config import settings

def fetch_all_movies() -> List[Dict[str, Any]]:
    resp = requests.get(settings.ghibli_films_url, timeout=10)
    resp.raise_for_status()
    movies = resp.json()
    for m in movies:
        m.setdefault("release_date", None)
        m.setdefault("rt_score", "0")
        m.setdefault("running_time", None)
    return movies
