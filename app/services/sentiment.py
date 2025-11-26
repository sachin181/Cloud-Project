# app/services/sentiment.py

from dataclasses import dataclass
from typing import Optional
import json
import requests

from ..config import settings


@dataclass
class SentimentResult:
    """
    label:  "positive" | "neutral" | "negative"
    score:  -1.0 .. 1.0  (negative .. positive)
    """
    label: str
    score: float


# -------------------------------------------------
# Simple local fallback model (no network needed)
# -------------------------------------------------

_POSITIVE_WORDS = [
    "good",
    "great",
    "amazing",
    "awesome",
    "love",
    "loved",
    "excellent",
    "fantastic",
    "enjoyed",
    "liked",
]

_NEGATIVE_WORDS = [
    "bad",
    "boring",
    "terrible",
    "awful",
    "hate",
    "hated",
    "disappointing",
    "disappointed",
    "slow",
    "did not like",
    "didn't like",
    "worst",
]


def _mock_analyze(text: str) -> SentimentResult:
    """
    Very simple keyword-based sentiment, used as a backup if OpenAI fails.
    """
    t = text.lower()
    score = 0.0

    for w in _POSITIVE_WORDS:
        if w in t:
            score += 0.2

    for w in _NEGATIVE_WORDS:
        if w in t:
            score -= 0.25

    # clamp to [-1, 1]
    score = max(min(score, 1.0), -1.0)

    if score > 0.1:
        label = "positive"
    elif score < -0.1:
        label = "negative"
    else:
        label = "neutral"

    return SentimentResult(label=label, score=score)


# -------------------------------------------------
# OpenAI integration (via /v1/chat/completions)
# -------------------------------------------------

def _openai_analyze(text: str) -> SentimentResult:
    """
    Use OpenAI's /v1/chat/completions API to classify sentiment.

    We ask the model to return STRICT JSON like:
      {"label": "negative", "score": -0.8}

    If anything goes wrong (HTTP error, bad JSON, etc.), we fall back to _mock_analyze.
    """
    api_key = settings.openai_api_key
    if not api_key:
        print("OPENAI_API_KEY not set – using mock sentiment.")
        return _mock_analyze(text)

    url = "https://api.openai.com/v1/chat/completions"

    system_prompt = (
        "You are a strict sentiment classifier for movie reviews.\n"
        "Read the review and return ONLY valid JSON, nothing else.\n"
        "The JSON must be exactly of the form:\n"
        '{\"label\": \"positive|neutral|negative\", \"score\": NUMBER}\n'
        "Where score is between -1.0 and 1.0 (negative = very negative, "
        "positive = very positive, 0 = neutral)."
    )

    payload = {
        "model": "gpt-4.1-mini",  # or gpt-4o-mini / gpt-3.5-turbo if needed
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        # helps push it towards JSON
        "response_format": {"type": "json_object"},
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        # Standard Chat Completions structure:
        # choices[0].message.content is the string we want
        choices = data.get("choices") or []
        if not choices:
            raise ValueError("No choices returned from OpenAI")

        raw_text = choices[0]["message"]["content"]

        # raw_text should now be JSON like: {"label": "negative", "score": -0.8}
        parsed = json.loads(raw_text)

        label = str(parsed["label"]).lower()
        if label not in {"positive", "neutral", "negative"}:
            raise ValueError(f"Invalid label from OpenAI: {label}")

        score = float(parsed["score"])
        score = max(min(score, 1.0), -1.0)

        return SentimentResult(label=label, score=score)

    except Exception as e:
        # For robustness in your demo: never crash, just fall back
        print("OpenAI sentiment call failed, falling back to mock:", repr(e))
        return _mock_analyze(text)


# -------------------------------------------------
# Public entry point used by your review endpoints
# -------------------------------------------------

def analyze_sentiment(text: str) -> SentimentResult:
    """
    Main function used by the rest of the app.

    If SENTIMENT_PROVIDER=openai in .env, use OpenAI.
    Otherwise use the local mock model.
    """
    provider = (settings.sentiment_provider or "").lower()
    if provider == "openai":
        return _openai_analyze(text)
    else:
        return _mock_analyze(text)
