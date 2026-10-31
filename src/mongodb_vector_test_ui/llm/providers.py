from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from mongodb_vector_test_ui.core.config import Settings, get_settings
from mongodb_vector_test_ui.embeddings.providers import embed_documents, embed_query

CHAT_PROVIDER_ALIASES = {"grok": "xai", "openai_compatible": "openai"}
PROVIDER_API_KEY_ENV = {
    "anthropic": "ANTHROPIC_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "openai": "OPENAI_API_KEY",
    "xai": "XAI_API_KEY",
}

# Model IDs that previously reached the provider but were denied for this API project.
# Keep this local guard small: provider model catalogs change, but these known-bad
# values should not trigger another opaque upstream 403 in the Streamlit test UI.
UNAVAILABLE_MODEL_HINTS = {
    "openai": {
        "gpt-4o-mini": "Use CHAT_MODEL=gpt-5.5, CHAT_MODEL=gpt-5.1 instead.",
        "gpt-5.4-mini": "Use CHAT_MODEL=gpt-5.5, or CHAT_MODEL=gpt-5.1 instead.",
        "gpt-5-mini": "Use CHAT_MODEL=gpt-5.5, or CHAT_MODEL=gpt-5.1 instead.",
    }
}


@dataclass(frozen=True)
class ChatModelConfig:
    provider: str
    model: str
    api_key: str
    base_url: str = ""
    temperature: float = 0.2
    max_tokens: int = 700
    timeout: int = 60
    max_retries: int = 2


class ModelProviderAdapter:
    """Keep retrieval models and generative chat models behind stable interfaces."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def embedding_provider(self) -> str:
        return self.settings.embedding_provider.lower()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return embed_documents(texts, self.settings)

    def embed_query(self, text: str) -> list[float]:
        return embed_query(text, self.settings)

    def create_chat_model(self, config: ChatModelConfig | None = None) -> Any:
        chat = config or chat_model_config_from_env()
        provider = normalize_chat_provider(chat.provider)
        if not chat.model:
            raise ValueError("CHAT_MODEL is required for a generative chat provider.")
        validate_chat_model(provider, chat.model)
        if not chat.api_key:
            key_name = provider_api_key_env(provider)
            raise ValueError(f"CHAT_API_KEY or {key_name} is required for {provider}.")

        try:
            from langchain.chat_models import init_chat_model
        except ImportError as exc:
            raise RuntimeError(
                "LangChain model support is not installed. "
                'Run python -m pip install -e ".[orchestration,<provider>]".'
            ) from exc

        kwargs: dict[str, Any] = {
            "api_key": chat.api_key,
            "temperature": chat.temperature,
            "max_tokens": chat.max_tokens,
            "timeout": chat.timeout,
            "max_retries": chat.max_retries,
        }
        if chat.base_url:
            kwargs["base_url"] = chat.base_url
        return init_chat_model(
            model=chat.model,
            model_provider=provider,
            **kwargs,
        )

    def create_langgraph_model(self, config: ChatModelConfig | None = None) -> Any:
        """Return the same BaseChatModel interface accepted by LangGraph nodes."""
        return self.create_chat_model(config)


def chat_model_config_from_env() -> ChatModelConfig:
    provider = normalize_chat_provider(os.getenv("CHAT_PROVIDER", "openai"))
    provider_key = os.getenv(provider_api_key_env(provider), "").strip()
    return ChatModelConfig(
        provider=provider,
        model=os.getenv("CHAT_MODEL", "").strip(),
        api_key=os.getenv("CHAT_API_KEY", "").strip() or provider_key,
        base_url=os.getenv("CHAT_BASE_URL", "").strip().rstrip("/"),
        temperature=_float_env("CHAT_TEMPERATURE", 0.0),
        max_tokens=_int_env("CHAT_MAX_TOKENS", 700),
        timeout=_int_env("CHAT_TIMEOUT_SECONDS", 60),
        max_retries=_int_env("CHAT_MAX_RETRIES", 2),
    )


def normalize_chat_provider(provider: str) -> str:
    normalized = provider.strip().lower()
    normalized = CHAT_PROVIDER_ALIASES.get(normalized, normalized)
    if not normalized:
        raise ValueError("CHAT_PROVIDER is required.")
    if normalized == "voyage":
        raise ValueError(
            "Voyage AI is an embedding/reranking provider, not a generative chat "
            "provider. Keep EMBEDDING_PROVIDER=voyage and configure CHAT_PROVIDER "
            "with OpenAI, Anthropic, xAI/Grok, or DeepSeek."
        )
    return normalized


def validate_chat_model(provider: str, model: str) -> None:
    provider = normalize_chat_provider(provider)
    model = model.strip()
    hint = UNAVAILABLE_MODEL_HINTS.get(provider, {}).get(model)
    if hint:
        raise ValueError(
            f"CHAT_MODEL={model} is not accessible for this {provider} API project. "
            f"{hint} Update the API process environment and restart FastAPI before "
            "testing from Streamlit again."
        )


def provider_api_key_env(provider: str) -> str:
    return PROVIDER_API_KEY_ENV.get(
        provider,
        f"{provider.upper().replace('-', '_')}_API_KEY",
    )


def safe_model_diagnostics() -> dict[str, Any]:
    try:
        config = chat_model_config_from_env()
        provider = normalize_chat_provider(config.provider)
        if config.model:
            validate_chat_model(provider, config.model)
        return {
            "chat_provider": provider,
            "chat_model": config.model,
            "chat_api_key_set": bool(config.api_key),
            "chat_base_url_set": bool(config.base_url),
            "chat_temperature": config.temperature,
            "chat_max_tokens": config.max_tokens,
        }
    except ValueError as exc:
        return {"chat_config_error": str(exc)}


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name, "").strip()
    return int(value) if value else default


def _float_env(name: str, default: float) -> float:
    value = os.getenv(name, "").strip()
    return float(value) if value else default
