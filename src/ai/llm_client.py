import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "groq").strip().lower()
DEFAULT_MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instant").strip()

_groq_client = None


def get_default_provider():
    return DEFAULT_PROVIDER


def get_default_model():
    return DEFAULT_MODEL


def get_groq_client():
    global _groq_client

    if _groq_client is None:
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise RuntimeError("GROQ_API_KEY not found in environment")
        _groq_client = Groq(api_key=groq_api_key)

    return _groq_client


def run_chat_completion(
    messages,
    model=None,
    temperature=0,
    max_tokens=500,
    provider=None,
):
    provider_name = (provider or DEFAULT_PROVIDER).strip().lower()
    model_name = model or DEFAULT_MODEL

    if provider_name == "groq":
        client = get_groq_client()

        completion = client.chat.completions.create(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=messages,
        )

        return completion.choices[0].message.content

    raise ValueError(f"Unsupported LLM provider: {provider_name}")