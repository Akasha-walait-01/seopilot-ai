# This file is our LLM abstraction layer
# Goal: agents will call ask_llm() and never talk to Gemini directly
# This makes it easy to swap providers later (rule from spec section 33)
# Using the new "google-genai" SDK (the old "google-generativeai" is deprecated)

from google import genai
from backend.config import settings

# create one shared client, only if key is present
_client = genai.Client(api_key=settings.gemini_api_key) if settings.gemini_api_key else None

# current stable model (as of Aug 2026)
DEFAULT_MODEL = "gemini-2.5-flash"


def ask_llm(prompt: str, model_name: str = DEFAULT_MODEL) -> str:
    """
    Send a prompt to the LLM and return plain text response.
    If no API key is set, return a clear message instead of crashing.
    """
    if not _client:
        return "LLM not configured. Please add GEMINI_API_KEY in .env file."

    try:
        response = _client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        return response.text
    except Exception as error:
        # never crash the app, just report the error clearly
        return f"LLM error: {str(error)}"