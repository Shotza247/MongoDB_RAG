FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DEFAULT_TIMEOUT=180 \
    PIP_RETRIES=10

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
RUN --mount=type=cache,id=mongodb-rag-api-pip,target=/root/.cache/pip \
    python -m pip install "."

COPY api ./api

FROM base AS api

RUN --mount=type=cache,id=mongodb-rag-mvp2-pip,target=/root/.cache/pip \
    python -m pip install ".[orchestration,openai]"

EXPOSE 8765

CMD ["python", "-m", "uvicorn", "mongodb_vector_test_ui.api.fastapi:app", "--host", "0.0.0.0", "--port", "8765", "--http", "h11"]

FROM base AS streamlit

RUN --mount=type=cache,id=mongodb-rag-streamlit-pip,target=/root/.cache/pip \
    python -m pip install "streamlit>=1.57,<1.64"

COPY templates/document-vector-pipeline/streamlit_app.py ./templates/document-vector-pipeline/streamlit_app.py

EXPOSE 8501

CMD ["python", "-m", "streamlit", "run", "templates/document-vector-pipeline/streamlit_app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]
