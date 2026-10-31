# GitHub Project Board

## Project Name

MongoDB RAG Profile Agent

## Project Description

Build a reproducible document-to-vector-search and grounded-answer system for the Profile Assistant/Profile Agent. The project starts with a local MongoDB Vector Search test UI, then adds reranking, LLM answer generation, and finally a production-ready API that can power the portfolio assistant.

## Suggested Views

### MVP Roadmap

Purpose: track work across MVP1, MVP2, and MVP3.

Fields:

- Status: Backlog, Ready, In Progress, In Review, Done
- MVP: MVP1, MVP2, MVP3
- Area: ingestion, retrieval, reranking, LLM, API, UI, docs, deployment
- Priority: P0, P1, P2

### Current Sprint

Purpose: keep the immediate working set small.

Suggested filter:

```text
status:open label:mvp1
```

### Bugs And Recovery

Purpose: track repeatable setup, API, embedding, MongoDB, deployment, and hosted runtime errors.

Suggested filter:

```text
status:open label:bug
```

## MVP Breakdown

### MVP1 - Retrieval Foundation

Outcome:

Users can load documents, extract text, preview chunks, store embeddings in MongoDB, and retrieve ranked chunks through vector search.

Primary areas:

- document ingestion
- chunking
- embeddings
- MongoDB vector storage
- vector retrieval
- test UI
- documentation and audit logs

### MVP2 - FastAPI And Grounded LLM Answers

Outcome:

Users can ask a question, retrieve relevant chunks, rerank them, and receive a concise LLM-generated answer with citations.

Primary areas:

- native typed FastAPI contracts
- reranker
- LLM provider configuration
- `/api/ask` or `/api/chat`
- citation mapping
- answer UI
- answer quality smoke tests

### MVP3 - Profile Agent API And Production Readiness

Outcome:

The Profile Assistant/Profile Agent becomes a hosted API that the portfolio chatbot can call reliably.

Primary areas:

- Google Drive read-only synchronization and approval flow
- hosted API
- auth/CORS strategy
- observability
- portfolio integration
- deployment smoke tests
- privacy and document access controls
