"""API key authentication middleware."""

import json
import time
from collections import defaultdict
from pathlib import Path

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from .config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# In-memory stores (replace with Redis/DB in production)
_valid_keys: dict[str, dict] = {}
_rate_counters: dict[str, list[float]] = defaultdict(list)


def load_api_keys():
    """Load API keys from file."""
    global _valid_keys
    path = Path(settings.api_keys_file)
    if path.exists():
        with open(path) as f:
            _valid_keys = json.load(f)


def _check_rate_limit(api_key: str):
    """Simple sliding-window rate limiter."""
    now = time.time()
    window = 60.0
    timestamps = _rate_counters[api_key]

    # Remove expired entries
    _rate_counters[api_key] = [t for t in timestamps if now - t < window]
    timestamps = _rate_counters[api_key]

    if len(timestamps) >= settings.rate_limit_per_minute:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {settings.rate_limit_per_minute}/min",
        )
    _rate_counters[api_key].append(now)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """Verify API key and enforce rate limits."""
    if not settings.require_auth:
        return "dev-mode"

    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key. Set X-API-Key header.")

    if api_key not in _valid_keys:
        raise HTTPException(status_code=403, detail="Invalid API key.")

    key_data = _valid_keys[api_key]
    if key_data.get("disabled"):
        raise HTTPException(status_code=403, detail="API key is disabled.")

    _check_rate_limit(api_key)
    return api_key
