import pytest

from mongodb_vector_test_ui.core.config import Settings
from mongodb_vector_test_ui.llm.providers import (
    ChatModelConfig,
    ModelProviderAdapter,
    normalize_chat_provider,
    safe_model_diagnostics,
    validate_chat_model,
)


def test_grok_alias_normalizes_to_xai():
    assert normalize_chat_provider("grok") == "xai"


def test_voyage_is_rejected_as_chat_provider():
    with pytest.raises(ValueError, match="embedding/reranking provider"):
        normalize_chat_provider("voyage")


def test_additional_langchain_provider_passes_through():
    assert normalize_chat_provider("google_genai") == "google_genai"


def test_adapter_keeps_voyage_embedding_provider():
    adapter = ModelProviderAdapter(Settings(embedding_provider="voyage"))
    assert adapter.embedding_provider == "voyage"


def test_chat_model_requires_model_before_importing_langchain():
    adapter = ModelProviderAdapter(Settings())
    config = ChatModelConfig(provider="openai", model="", api_key="test-key")
    with pytest.raises(ValueError, match="CHAT_MODEL"):
        adapter.create_chat_model(config)


def test_known_inaccessible_openai_model_fails_before_provider_call():
    with pytest.raises(ValueError, match="gpt-5.4-mini"):
        validate_chat_model("openai", "gpt-5.4-mini")


def test_safe_model_diagnostics_reports_known_inaccessible_model(monkeypatch):
    monkeypatch.setenv("CHAT_PROVIDER", "openai")
    monkeypatch.setenv("CHAT_MODEL", "gpt-5.4-mini")

    diagnostics = safe_model_diagnostics()

    assert "chat_config_error" in diagnostics
    assert "gpt-5.4-mini" in diagnostics["chat_config_error"]
    assert "gpt-5.5" in diagnostics["chat_config_error"]
