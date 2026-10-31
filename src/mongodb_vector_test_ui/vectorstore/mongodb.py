from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import OperationFailure, PyMongoError

from mongodb_vector_test_ui.core.config import Settings

FILTER_FIELDS = ("metadata.source_id", "metadata.title", "metadata.section", "chunk_id")


class MongoVectorStore:
    def __init__(self, settings: Settings) -> None:
        if not settings.mongodb_uri:
            raise ValueError("MONGODB_URI is required.")

        self.settings = settings
        self.client = MongoClient(settings.mongodb_uri)
        self.collection: Collection = self.client[settings.mongodb_db][settings.mongodb_collection]

    def ping(self) -> bool:
        self.client.admin.command("ping")
        return True

    def count_documents(self) -> int:
        return self.collection.count_documents({})

    def list_databases(self) -> list[dict]:
        names = self.client.list_database_names()
        return [{"name": name} for name in sorted(names)]

    def list_collections(self, database: str | None = None) -> list[dict]:
        db_name = database or self.settings.mongodb_db
        collection_names = self.client[db_name].list_collection_names()
        return [{"name": name} for name in sorted(collection_names)]

    def collection_summary(self) -> dict:
        summary = {
            "database": self.settings.mongodb_db,
            "collection": self.settings.mongodb_collection,
            "document_count": None,
            "regular_indexes": [],
            "search_indexes": [],
            "sample_fields": [],
        }
        try:
            summary["document_count"] = self.collection.estimated_document_count()
        except PyMongoError as exc:
            summary["document_count_error"] = str(exc)

        try:
            summary["regular_indexes"] = [_serializable(index) for index in self.collection.list_indexes()]
        except PyMongoError as exc:
            summary["regular_indexes_error"] = str(exc)

        try:
            summary["search_indexes"] = self.list_vector_indexes()
        except PyMongoError as exc:
            summary["search_indexes_error"] = str(exc)

        try:
            sample = self.collection.find_one({}, projection={self.settings.vector_field: 0})
            summary["sample_fields"] = sorted(sample.keys()) if isinstance(sample, dict) else []
            metadata = sample.get("metadata") if isinstance(sample, dict) else None
            summary["sample_metadata_fields"] = sorted(metadata.keys()) if isinstance(metadata, dict) else []
        except PyMongoError as exc:
            summary["sample_fields_error"] = str(exc)

        try:
            source_ids = sorted(str(value) for value in self.collection.distinct("source_id") if value)
            summary["source_ids"] = source_ids[:25]
            summary["source_id_count"] = len(source_ids)
        except PyMongoError as exc:
            summary["source_ids_error"] = str(exc)

        try:
            titles = sorted(str(value) for value in self.collection.distinct("metadata.title") if value)
            summary["titles"] = titles[:25]
            summary["title_count"] = len(titles)
        except PyMongoError as exc:
            summary["titles_error"] = str(exc)

        return summary

    def list_vector_indexes(self) -> list[dict]:
        return [_serializable(index) for index in self.collection.list_search_indexes()]

    def desired_vector_index_model(self) -> dict:
        return {
            "name": self.settings.vector_index_name,
            "type": "vectorSearch",
            "definition": self.desired_vector_index_definition(),
        }

    def desired_vector_index_definition(self) -> dict:
        return {
            "fields": [
                {
                    "type": "vector",
                    "path": self.settings.vector_field,
                    "numDimensions": self.settings.vector_dimensions,
                    "similarity": "cosine",
                },
                {"type": "filter", "path": "metadata.source_id"},
                {"type": "filter", "path": "metadata.title"},
                {"type": "filter", "path": "metadata.section"},
                {"type": "filter", "path": "chunk_id"},
            ]
        }

    def ensure_vector_index(self) -> dict:
        model = self.desired_vector_index_model()

        indexes = self.list_vector_indexes()
        existing = next(
            (index for index in indexes if index.get("name") == self.settings.vector_index_name),
            None,
        )
        if existing:
            available_paths = _filter_paths_from_index(existing)
            missing_paths = sorted(set(FILTER_FIELDS) - available_paths)
            return {
                "created": False,
                "message": "Vector index already exists.",
                "available_filter_paths": sorted(available_paths),
                "missing_filter_paths": missing_paths,
                "index": model,
            }

        try:
            self.collection.create_search_index(model=model)
        except OperationFailure as exc:
            return {"created": False, "message": str(exc), "index": model}
        return {"created": True, "message": "Vector index creation requested.", "index": model}

    def update_vector_index(self) -> dict:
        definition = self.desired_vector_index_definition()
        self.collection.update_search_index(self.settings.vector_index_name, definition)
        return {
            "updated": True,
            "message": "Vector index update requested.",
            "index_name": self.settings.vector_index_name,
            "definition": definition,
        }

    def vector_index_filter_paths(self) -> set[str]:
        indexes = self.list_vector_indexes()
        existing = next(
            (index for index in indexes if index.get("name") == self.settings.vector_index_name),
            None,
        )
        return _filter_paths_from_index(existing or {})

    def replace_source_chunks(self, source_id: str, chunks: list[dict], embeddings: list[list[float]]) -> int:
        if len(chunks) != len(embeddings):
            raise ValueError("Chunk and embedding counts do not match.")

        records = []
        for chunk, embedding in zip(chunks, embeddings):
            records.append({**chunk, self.settings.vector_field: embedding})

        self.collection.delete_many({"source_id": source_id})
        if records:
            self.collection.insert_many(records)
        return len(records)

    def vector_search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        min_score: float = 0.6,
        num_candidates: int | None = None,
        exact: bool = False,
        filters: dict | None = None,
    ) -> list[dict]:
        pipeline = build_vector_search_pipeline(
            self.settings,
            query_embedding=query_embedding,
            top_k=top_k,
            min_score=min_score,
            num_candidates=num_candidates,
            exact=exact,
            filters=filters,
        )
        return list(self.collection.aggregate(pipeline))


def build_vector_search_pipeline(
    settings: Settings,
    query_embedding: list[float],
    top_k: int = 5,
    min_score: float = 0.6,
    num_candidates: int | None = None,
    exact: bool = False,
    filters: dict | None = None,
) -> list[dict]:
    vector_stage = {
        "index": settings.vector_index_name,
        "path": settings.vector_field,
        "queryVector": query_embedding,
        "limit": top_k,
    }
    if exact:
        vector_stage["exact"] = True
    else:
        vector_stage["numCandidates"] = _num_candidates(
            top_k=top_k,
            requested=num_candidates,
            fallback=settings.vector_num_candidates,
        )

    filter_document = _filter_document(filters or {})
    if filter_document:
        vector_stage["filter"] = filter_document

    pipeline = [
        {"$vectorSearch": vector_stage},
        {
            "$project": {
                "_id": 0,
                "chunk_id": 1,
                "source_id": 1,
                "text": 1,
                "metadata": 1,
                "score": {"$meta": "vectorSearchScore"},
            }
        },
        {"$match": {"score": {"$gte": min_score}}},
    ]
    return pipeline


def _num_candidates(top_k: int, requested: int | None, fallback: int) -> int:
    candidate_count = requested if requested is not None else max(fallback, top_k * 20)
    return min(max(candidate_count, top_k), 10000)


def _filter_document(filters: dict) -> dict:
    clauses = []
    for field in FILTER_FIELDS:
        values = _clean_filter_values(filters.get(field))
        if not values:
            continue
        if len(values) == 1:
            clauses.append({field: values[0]})
        else:
            clauses.append({field: {"$in": values}})
    if not clauses:
        return {}
    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}


def _clean_filter_values(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        raw_values = value.split(",")
    elif isinstance(value, list):
        raw_values = value
    else:
        raw_values = [value]
    cleaned = [str(item).strip() for item in raw_values]
    return [item for item in cleaned if item]


def _filter_paths_from_index(index: dict) -> set[str]:
    definition = index.get("latestDefinition") or index.get("definition") or {}
    fields = definition.get("fields") or []
    return {
        str(field.get("path"))
        for field in fields
        if isinstance(field, dict) and field.get("type") == "filter" and field.get("path")
    }


def _serializable(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): _serializable(child) for key, child in value.items()}
    if isinstance(value, list):
        return [_serializable(child) for child in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value
