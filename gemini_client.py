"""Centralized Gemini client with auto-fallback across models.

Why: Google deprecates model names regularly (gemini-1.5-flash was retired in early 2026).
We try a list of current model names in priority order. Returns text or raises last error.
"""
import google.generativeai as genai
from cloud_storage import load_data

# Priority list — try newest/cheapest first, fall back if unavailable
MODEL_CANDIDATES = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.5-flash-lite",
    "gemini-flash-latest",
    "gemini-pro-latest",
]


def _get_key():
    d = load_data()
    return ((d or {}).get("settings") or {}).get("gemini_key", "")


def _configure():
    key = _get_key()
    if not key:
        raise RuntimeError("No Gemini API key configured. Add one in Profile.")
    genai.configure(api_key=key)


def generate_text(prompt: str, system: str = "") -> str:
    """Generate text. Returns the model's text output. Raises on failure."""
    _configure()
    full = (f"{system}\n\n{prompt}" if system else prompt)
    last_err = None
    for model_name in MODEL_CANDIDATES:
        try:
            model = genai.GenerativeModel(model_name)
            resp = model.generate_content(full)
            text = (getattr(resp, "text", "") or "").strip()
            if text:
                return text
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"All Gemini models failed. Last error: {last_err}")


def generate_with_image(prompt: str, image_bytes: bytes, mime: str = "image/jpeg") -> str:
    """Multimodal: prompt + image. Returns text."""
    _configure()
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
            continue
    raise RuntimeError(f"All Gemini vision models failed. Last error: {last_err}")


def chat(history: list, user_msg: str, system: str = "") -> str:
    """Multi-turn chat. history is [(role, text), ...] where role in 'user'|'model'."""
    _configure()
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
            continue
    raise RuntimeError(f"All Gemini models failed. Last error: {last_err}")
