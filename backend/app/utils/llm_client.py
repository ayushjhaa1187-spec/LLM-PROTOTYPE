from openai import OpenAI
from app.config import settings

def get_llm_client():
    """Returns an OpenAI-compatible client based on configured provider."""
    provider = settings.LLM_PROVIDER.lower()
    
    if provider == "groq":
        return OpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1"
        )
    elif provider == "together":
        return OpenAI(
            api_key=settings.TOGETHER_API_KEY,
            base_url="https://api.together.xyz/v1"
        )
    elif provider == "gemini":
        # Gemini via OpenAI compatibility layer
        return OpenAI(
            api_key=settings.GEMINI_API_KEY,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
    elif provider == "mistral":
        return OpenAI(
            api_key=settings.MISTRAL_API_KEY,
            base_url="https://api.mistral.ai/v1"
        )
    elif provider == "openrouter":
        return OpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "FAR-Copilot",
            }
        )
    else:
        # Default to OpenAI
        return OpenAI(api_key=settings.OPENAI_API_KEY)

def get_model_name():
    """Returns the recommended model name for the selected provider."""
    provider = settings.LLM_PROVIDER.lower()
    
    if provider == "groq":
        return "llama-3.3-70b-versatile"
    elif provider == "together":
        return "meta-llama/Llama-3.3-70B-Instruct-Turbo"
    elif provider == "gemini":
        return "gemini-2.0-flash"
    elif provider == "mistral":
        return "mistral-small-latest"
    elif provider == "openrouter":
        return "meta-llama/llama-3.1-8b-instruct:free"
    else:
        return "gpt-4o-mini"
