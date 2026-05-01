"""Centralized Gemini client.

Smart behavior:
- Falls back through model candidates (deprecated names get retired regularly)
- Detects rate-limit / quota / network errors and stops retrying immediately (no credit burn)
- Uses baked-in key as default; user can override in Profile
- Caches successful responses for 1 hour (saves quota on repeat queries)
- Returns clean error class GeminiUnavailable so callers can show a friendly fallback
"""
import time
import hashlib
import google.generativeai as genai
from cloud_storage import load_data

# Priority list — try newest/cheapest first
MODEL_CANDIDATES = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.5-flash-lite",
    "gemini-flash-latest",
    "gemini-pro-latest",
]

# Baked-in key (Joel's free tier)
DEFAULT_KEY = "AIzaSyD2osEMCaQagKBaPZqfq_jMDU-cS4HCjCw"

# In-memory cache: hash -> (timestamp, response)
_RESPONSE_CACHE = {}
_CACHE_TTL = 3600  # 1 hour

# Track quota-exceeded state to avoid hammering
_QUOTA_BLOCKED_UNTIL = 0


class GeminiUnavailable(Exception):
    """Raised when Gemini is unreachable for a recoverable reason (quota, network)."""
    def __init__(self, message: str, reason: str = "unknown"):
        super().__init__(message)
        self.reason = reason  # 'quota' | 'no_key' | 'network' | 'unknown'


def _get_key() -> str:
    try:
        d = load_data() or {}
        user_key = ((d.get("settings") or {}).get("gemini_key") or "").strip()
        return user_key or DEFAULT_KEY
    except Exception:
        return DEFAULT_KEY


def _configure():
    key = _get_key()
    if not key:
        raise GeminiUnavailable("No Gemini API key configured.", reason="no_key")
    genai.configure(api_key=key)


def _is_quota_error(e: Exception) -> bool:
    msg = str(e).lower()
    return any(s in msg for s in ["429", "quota", "rate limit", "rate_limit", "exceeded"])


def _is_network_error(e: Exception) -> bool:
    msg = str(e).lower()
    return any(s in msg for s in ["timeout", "connection", "unreachable", "dns", "ssl"])


def _cache_key(prompt: str, system: str = "") -> str:
    return hashlib.sha256(f"{system}||{prompt}".encode("utf-8")).hexdigest()[:32]


def _cache_get(key: str):
    entry = _RESPONSE_CACHE.get(key)
    if not entry:
        return None
    ts, value = entry
    if time.time() - ts > _CACHE_TTL:
        _RESPONSE_CACHE.pop(key, None)
        return None
    return value


def _cache_set(key: str, value: str):
    _RESPONSE_CACHE[key] = (time.time(), value)
    # Trim cache to last 100 entries
    if len(_RESPONSE_CACHE) > 100:
        oldest = sorted(_RESPONSE_CACHE.items(), key=lambda kv: kv[1][0])[:20]
        for k, _ in oldest:
            _RESPONSE_CACHE.pop(k, None)


def is_available() -> bool:
    """Quick check — true if no quota block in effect."""
    return time.time() >= _QUOTA_BLOCKED_UNTIL


def quota_status() -> dict:
    """Returns {'available': bool, 'blocked_for_seconds': int}."""
    remaining = max(0, int(_QUOTA_BLOCKED_UNTIL - time.time()))
    return {"available": remaining == 0, "blocked_for_seconds": remaining}


def _block_quota(minutes: int = 5):
    global _QUOTA_BLOCKED_UNTIL
    _QUOTA_BLOCKED_UNTIL = time.time() + minutes * 60


def generate_text(prompt: str, system: str = "", use_cache: bool = True) -> str:
    """Generate text. Raises GeminiUnavailable on failure."""
    if use_cache:
        ck = _cache_key(prompt, system)
        cached = _cache_get(ck)
        if cached is not None:
            return cached

    if not is_available():
        raise GeminiUnavailable(
            f"Gemini quota cooldown — try again in {int(_QUOTA_BLOCKED_UNTIL - time.time())}s.",
            reason="quota",
        )

    try:
        _configure()
    except GeminiUnavailable:
        raise

    full = f"{system}\n\n{prompt}" if system else prompt
    last_err = None
    for model_name in MODEL_CANDIDATES:
        try:
            model = genai.GenerativeModel(model_name)
            resp = model.generate_content(full)
            text = (getattr(resp, "text", "") or "").strip()
            if text:
                if use_cache:
                    _cache_set(_cache_key(prompt, system), text)
                return text
        except Exception as e:
            last_err = e
            if _is_quota_error(e):
                _block_quota(5)  # back off for 5 minutes
                raise GeminiUnavailable(
                    "Gemini quota exceeded. Using local intelligence for now.",
                    reason="quota",
                )
            if _is_network_error(e):
                raise GeminiUnavailable("Network issue reaching Gemini.", reason="network")
            continue
    raise GeminiUnavailable(f"Gemini models all failed: {last_err}", reason="unknown")


def generate_with_image(prompt: str, image_bytes: bytes, mime: str = "image/jpeg") -> str:
    """Multimodal: prompt + image."""
    if not is_available():
        raise GeminiUnavailable("Gemini quota cooldown.", reason="quota")
    try:
        _configure()
    except GeminiUnavailable:
        raise

    last_err = None
    for model_name in MODEL_CANDIDATES:
        try:
            model = genai.GenerativeModel(model_name)
            resp = model.generate_content([
                prompt,
                {"mime_type": mime, "data": image_bytes},
            ])
            text = (getattr(resp, "text", "") or "").strip()
            if text:
                return text
        except Exception as e:
            last_err = e
            if _is_quota_error(e):
                _block_quota(5)
                raise GeminiUnavailable("Quota exceeded.", reason="quota")
            if _is_network_error(e):
                raise GeminiUnavailable("Network issue.", reason="network")
            continue
    raise GeminiUnavailable(f"Vision models failed: {last_err}", reason="unknown")


def chat(history: list, user_msg: str, system: str = "") -> str:
    """Multi-turn chat."""
    if not is_available():
        raise GeminiUnavailable(
            f"Gemini quota cooldown — try again in {int(_QUOTA_BLOCKED_UNTIL - time.time())}s.",
            reason="quota",
        )
    try:
        _configure()
    except GeminiUnavailable:
        raise

    last_err = None
    for model_name in MODEL_CANDIDATES:
        try:
            model = genai.GenerativeModel(model_name, system_instruction=system or None)
            chat_session = model.start_chat(history=[
                {"role": r, "parts": [t]} for r, t in (history or []) if t
            ])
            resp = chat_session.send_message(user_msg)
            text = (getattr(resp, "text", "") or "").strip()
            if text:
                return text
        except Exception as e:
            last_err = e
            if _is_quota_error(e):
                _block_quota(5)
                raise GeminiUnavailable("Quota exceeded.", reason="quota")
            if _is_network_error(e):
                raise GeminiUnavailable("Network issue.", reason="network")
            continue
    raise GeminiUnavailable(f"Chat models failed: {last_err}", reason="unknown")
