import logging
from typing import Callable, Optional

MAX_QUERY_LENGTH = 200

# Every run writes what happened to app.log, so problems can be checked later.
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("music_ai")


def check_query(query: str) -> Optional[str]:
    """Input guardrail: return an error message if the request is bad, else None."""
    if not query.strip():
        return "Please type what kind of music you want."
    if len(query) > MAX_QUERY_LENGTH:
        return f"Please keep your request under {MAX_QUERY_LENGTH} characters."
    return None


def safe_ai_call(ai_function: Callable, *args, fallback):
    """Call Gemini, but if it fails (busy, no internet, bad key), return the fallback instead of crashing."""
    try:
        return ai_function(*args)
    except Exception as error:
        logger.error("AI call %s failed: %s", ai_function.__name__, error)
        return fallback