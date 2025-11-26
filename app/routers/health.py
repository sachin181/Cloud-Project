from fastapi import APIRouter
import requests
from ..config import settings

router = APIRouter()

@router.get("/healthz")
def healthz():
    try:
        requests.get(settings.ghibli_films_url, timeout=3)
        upstream = "reachable"
    except Exception:
        upstream = "unreachable"
    return {"status": "ok", "upstream": upstream, "version": settings.version}
