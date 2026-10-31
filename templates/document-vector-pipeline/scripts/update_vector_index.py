import argparse
import os
import time

from dotenv import load_dotenv
from pymongo import MongoClient

FILTER_FIELDS = ("metadata.source_id", "metadata.title", "metadata.section", "chunk_id")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create or update a MongoDB Atlas Vector Search index for a RAG collection."
    )
    parser.add_argument("--database", default="", help="MongoDB database name.")
    parser.add_argument("--collection", default="", help="MongoDB collection name.")
    parser.add_argument("--wait", action="store_true", help="Poll until the vector index is READY/queryable.")
    parser.add_argument("--timeout", type=int, default=600, help="Maximum seconds to wait with --wait.")
    args = parser.parse_args()

    load_dotenv(override=True)

    mongodb_uri = _required("MONGODB_URI")
    database = args.database or _required("MONGODB_DB")
    collection_name = args.collection or _required("MONGODB_COLLECTION")
    index_name = os.getenv("VECTOR_INDEX_NAME", "profile_vector_index").strip()
    vector_field = os.getenv("VECTOR_FIELD", "embedding").strip()
    vector_dimensions = int(os.getenv("VECTOR_DIMENSIONS", "1024"))

    client = MongoClient(mongodb_uri)
    collection = client[database][collection_name]
    client.admin.command("ping")

    definition = _index_definition(
        vector_field=vector_field,
        vector_dimensions=vector_dimensions,
    )
    existing = _find_index(collection, index_name)

    if existing:
        print(f"Updating existing vector index: {index_name}")
        collection.update_search_index(index_name, definition)
    else:
        print(f"Creating vector index: {index_name}")
        collection.create_search_index(
            {
                "name": index_name,
                "type": "vectorSearch",
                "definition": definition,
            }
        )

    print(f"Desired filter paths: {list(FILTER_FIELDS)}")

    final_index = _wait_until_ready(collection, index_name, args.timeout) if args.wait else _find_index(
        collection,
        index_name,
    )
    final_paths = sorted(_filter_paths_from_index(final_index or {}))
    print(f"Current filter paths: {final_paths}")

    missing_paths = sorted(set(FILTER_FIELDS) - set(final_paths))
    if missing_paths:
        print(f"Missing filter paths: {missing_paths}")
        raise SystemExit(2)

    if final_index:
        print(f"Index status: {final_index.get('status', 'unknown')}")
        print(f"Index queryable: {final_index.get('queryable', 'unknown')}")

    print("Vector index closeout check passed.")


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SystemExit(f"{name} is required.")
    return value


def _index_definition(vector_field: str, vector_dimensions: int) -> dict:
    return {
        "fields": [
            {
                "type": "vector",
                "path": vector_field,
                "numDimensions": vector_dimensions,
                "similarity": "cosine",
            },
            {"type": "filter", "path": "metadata.source_id"},
            {"type": "filter", "path": "metadata.title"},
            {"type": "filter", "path": "metadata.section"},
            {"type": "filter", "path": "chunk_id"},
        ]
    }


def _find_index(collection, index_name: str) -> dict | None:
    indexes = collection.list_search_indexes()
    return next((index for index in indexes if index.get("name") == index_name), None)


def _wait_until_ready(collection, index_name: str, timeout_seconds: int) -> dict:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        index = _find_index(collection, index_name)
        if index and index.get("status") == "READY" and index.get("queryable") is True:
            return index

        status = index.get("status", "not found") if index else "not found"
        queryable = index.get("queryable", "unknown") if index else "unknown"
        print(f"Waiting for index readiness: status={status}, queryable={queryable}")
        time.sleep(10)

    raise TimeoutError("Timed out waiting for vector index readiness.")


def _filter_paths_from_index(index: dict) -> set[str]:
    definition = index.get("latestDefinition") or index.get("definition") or {}
    fields = definition.get("fields") or []
    return {
        str(field.get("path"))
        for field in fields
        if isinstance(field, dict) and field.get("type") == "filter" and field.get("path")
    }


if __name__ == "__main__":
    main()
