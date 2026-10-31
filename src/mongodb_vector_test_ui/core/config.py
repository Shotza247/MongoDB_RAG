import os
from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


@dataclass(frozen=True)
class Settings:
    env_file: str = ""
    app_env: str = "local"
    mongodb_uri: str = ""
    mongodb_db: str = "RAG_with_MongoDB"
    mongodb_collection: str = "profile_chunks"
    vector_index_name: str = "profile_vector_index"
    vector_field: str = "embedding"
    vector_dimensions: int = 1024
    vector_num_candidates: int = 150
    embedding_provider: str = "voyage"
    voyage_base_url: str = "https://ai.mongodb.com/v1"
    voyage_api_key: str = ""
    voyage_model: str = "voyage-context-4"
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"


INVALID_DATABASE_CHARS = frozenset('/\\."$\x00')


@lru_cache
def get_settings() -> Settings:
    env_file = Path(os.getenv("ENV_FILE", Path.cwd() / ".env")).expanduser().resolve()
    if load_dotenv is not None:
        load_dotenv(env_file, override=True)
    return Settings(
        env_file=str(env_file),
        app_env=_str("APP_ENV", Settings.app_env),
        mongodb_uri=_str("MONGODB_URI", Settings.mongodb_uri),
        mongodb_db=_str("MONGODB_DB", Settings.mongodb_db),
        mongodb_collection=_str("MONGODB_COLLECTION", Settings.mongodb_collection),
        vector_index_name=_str("VECTOR_INDEX_NAME", Settings.vector_index_name),
        vector_field=_str("VECTOR_FIELD", Settings.vector_field),
        vector_dimensions=_int("VECTOR_DIMENSIONS", Settings.vector_dimensions),
        vector_num_candidates=_int("VECTOR_NUM_CANDIDATES", Settings.vector_num_candidates),
        embedding_provider=_str("EMBEDDING_PROVIDER", Settings.embedding_provider),
        voyage_base_url=_str("VOYAGE_BASE_URL", Settings.voyage_base_url).rstrip("/"),
        voyage_api_key=_str("VOYAGE_API_KEY", Settings.voyage_api_key),
        voyage_model=_str("VOYAGE_MODEL", Settings.voyage_model),
        openai_api_key=_str("OPENAI_API_KEY", Settings.openai_api_key),
        openai_embedding_model=_str("OPENAI_EMBEDDING_MODEL", Settings.openai_embedding_model),
    )


def _str(name: str, default: str) -> str:
    return os.getenv(name, default).strip()


def _int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return int(value)


def safe_diagnostics(settings: Settings) -> dict:
    host = mongodb_host(settings.mongodb_uri)
    return {
        "env_file": settings.env_file,
        "mongodb_uri_set": bool(settings.mongodb_uri),
        "mongodb_uri_length": len(settings.mongodb_uri),
        "mongodb_uri_starts_valid_scheme": settings.mongodb_uri.startswith(
            ("mongodb+srv://", "mongodb://")
        ),
        "mongodb_uri_at_count": settings.mongodb_uri.count("@"),
        "mongodb_host": host,
        "mongodb_host_looks_placeholder": _looks_placeholder(host),
        "mongodb_db": settings.mongodb_db,
        "mongodb_collection": settings.mongodb_collection,
        "vector_index_name": settings.vector_index_name,
        "vector_field": settings.vector_field,
        "vector_dimensions": settings.vector_dimensions,
        "embedding_provider": settings.embedding_provider,
        "voyage_base_url": settings.voyage_base_url if settings.embedding_provider == "voyage" else None,
        "voyage_api_key_set": bool(settings.voyage_api_key),
        "voyage_model": settings.voyage_model,
        "openai_api_key_set": bool(settings.openai_api_key),
        "openai_embedding_model": settings.openai_embedding_model,
    }


def validate_settings(settings: Settings) -> list[str]:
    issues: list[str] = []
    host = mongodb_host(settings.mongodb_uri)
    if not settings.mongodb_uri:
        issues.append("MONGODB_URI is missing.")
    elif not host:
        issues.append(
            "MONGODB_URI is set but malformed. It must start with mongodb+srv:// or "
            "mongodb:// and include username:password@cluster-host. If the password has "
            "special characters such as #, @, /, ?, :, or %, URL-encode the password."
        )
    elif _looks_placeholder(host):
        issues.append(
            "MONGODB_URI still looks like a placeholder. Replace CLUSTER.mongodb.net with "
            "the exact Atlas hostname from Connect, for example cluster0.xxxxx.mongodb.net."
        )

    provider = settings.embedding_provider.lower()
    if provider == "voyage" and not settings.voyage_api_key:
        issues.append("VOYAGE_API_KEY is missing for EMBEDDING_PROVIDER=voyage.")
    if provider == "openai" and not settings.openai_api_key:
        issues.append("OPENAI_API_KEY is missing for EMBEDDING_PROVIDER=openai.")
    return issues


def with_mongodb_target(settings: Settings, database: str = "", collection: str = "") -> Settings:
    database = _clean_database_name(database or settings.mongodb_db)
    collection = _clean_collection_name(collection or settings.mongodb_collection)
    return replace(settings, mongodb_db=database, mongodb_collection=collection)


def mongodb_host(uri: str) -> str:
    if not uri:
        return ""
    parsed = urlparse(uri)
    return parsed.hostname or ""


def _looks_placeholder(value: str) -> bool:
    lowered = value.lower()
    return "cluster.mongodb.net" in lowered or "user" in lowered or "password" in lowered


def _clean_database_name(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("MongoDB database name is required.")
    if len(cleaned.encode()) > 63:
        raise ValueError("MongoDB database name must be 63 bytes or fewer.")
    if any(char in INVALID_DATABASE_CHARS for char in cleaned):
        raise ValueError('MongoDB database name cannot contain /, \\, ., ", $, or null characters.')
    return cleaned


def _clean_collection_name(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("MongoDB collection name is required.")
    if "\x00" in cleaned:
        raise ValueError("MongoDB collection name cannot contain null characters.")
    if cleaned.startswith("system."):
        raise ValueError("System collections are not valid RAG test UI targets.")
    return cleaned
