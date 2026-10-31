import argparse
import time

from pymongo.errors import OperationFailure

from mongodb_vector_test_ui.core.config import (
    get_settings,
    validate_settings,
    with_mongodb_target,
)
from mongodb_vector_test_ui.vectorstore.mongodb import FILTER_FIELDS, MongoVectorStore


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create or update the MongoDB Atlas Vector Search index used by the RAG test UI."
    )
    parser.add_argument("--database", default="", help="MongoDB database name. Defaults to .env MONGODB_DB.")
    parser.add_argument("--collection", default="", help="MongoDB collection name. Defaults to .env MONGODB_COLLECTION.")
    parser.add_argument("--wait", action="store_true", help="Poll until the vector index is READY/queryable.")
    parser.add_argument("--timeout", type=int, default=600, help="Maximum seconds to wait with --wait.")
    args = parser.parse_args()

    settings = with_mongodb_target(get_settings(), database=args.database, collection=args.collection)
    issues = validate_settings(settings)
    if issues:
        print("Configuration issues:")
        for issue in issues:
            print(f"- {issue}")
        raise SystemExit(1)

    store = MongoVectorStore(settings)
    store.ping()

    existing = _find_index(store)
    if existing:
        before_paths = sorted(store.vector_index_filter_paths())
        print(f"Updating existing vector index: {settings.vector_index_name}")
        print(f"Existing filter paths: {before_paths}")
        result = store.update_vector_index()
    else:
        print(f"Creating vector index: {settings.vector_index_name}")
        result = store.ensure_vector_index()

    print(result["message"])
    print(f"Desired filter paths: {list(FILTER_FIELDS)}")

    if args.wait:
        final_index = _wait_until_ready(store, timeout_seconds=args.timeout)
    else:
        final_index = _find_index(store)

    final_paths = sorted(store.vector_index_filter_paths())
    print(f"Current filter paths: {final_paths}")
    missing_paths = sorted(set(FILTER_FIELDS) - set(final_paths))
    if missing_paths:
        print(f"Missing filter paths: {missing_paths}")
        raise SystemExit(2)

    if final_index:
        print(f"Index status: {final_index.get('status', 'unknown')}")
        print(f"Index queryable: {final_index.get('queryable', 'unknown')}")

    print("Vector index closeout check passed.")


def _find_index(store: MongoVectorStore) -> dict | None:
    indexes = store.list_vector_indexes()
    return next(
        (index for index in indexes if index.get("name") == store.settings.vector_index_name),
        None,
    )


def _wait_until_ready(store: MongoVectorStore, timeout_seconds: int) -> dict:
    deadline = time.monotonic() + timeout_seconds
    last_error = ""
    while time.monotonic() < deadline:
        try:
            index = _find_index(store)
        except OperationFailure as exc:
            last_error = str(exc)
            time.sleep(10)
            continue

        if index and index.get("status") == "READY" and index.get("queryable") is True:
            return index

        status = index.get("status", "not found") if index else "not found"
        queryable = index.get("queryable", "unknown") if index else "unknown"
        print(f"Waiting for index readiness: status={status}, queryable={queryable}")
        time.sleep(10)

    if last_error:
        raise TimeoutError(f"Timed out waiting for vector index readiness. Last error: {last_error}")
    raise TimeoutError("Timed out waiting for vector index readiness.")


if __name__ == "__main__":
    main()
