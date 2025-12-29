from .base import GraphProvider
from .openai_provider import OpenAIProvider
from .ollama_provider import OllamaProvider


def get_provider(provider_name: str, settings) -> GraphProvider:
    name = (provider_name or "").strip().lower()

    if name == "ollama":
        return OllamaProvider(base_url=settings.ollama_base_url, model=settings.ollama_model)

    if name == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is missing in .env")
        return OpenAIProvider(api_key=settings.openai_api_key, model=settings.openai_model)

    raise ValueError(f"Unknown provider: {provider_name}")
