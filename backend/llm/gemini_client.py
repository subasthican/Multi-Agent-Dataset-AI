import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from google import genai

# Repo-root .env (backend/llm/gemini_client.py -> llm -> backend -> repo root),
# so the key can live in one place alongside the rest of the project's .env.
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

DEFAULT_MODEL_NAME = "gemini-3.5-flash"


class LLMUnavailableError(Exception):
    """Raised when the LLM cannot be reached (no key, network/API error)."""


@lru_cache(maxsize=1)
def get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise LLMUnavailableError("GEMINI_API_KEY is not set")
    return genai.Client(api_key=api_key)


def generate_response(prompt: str) -> str:
    model_name = os.getenv("GEMINI_MODEL", DEFAULT_MODEL_NAME)
    try:
        client = get_client()
        response = client.models.generate_content(model=model_name, contents=prompt)
    except LLMUnavailableError:
        raise
    except Exception as exc:  # network/API errors from the SDK
        raise LLMUnavailableError(str(exc)) from exc

    if not response.text:
        raise LLMUnavailableError("empty response from LLM")
    return response.text
