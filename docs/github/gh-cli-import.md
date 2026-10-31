# GitHub CLI Import Guide

Use this after the folder is initialized as a Git repository and pushed to GitHub.

## 1. Create Labels

Fast path:

```powershell
.\scripts\create_github_mvp_plan.ps1 -DryRun
.\scripts\create_github_mvp_plan.ps1
```

Manual path:

```powershell
gh label create mvp --description "MVP scoped work"
gh label create mvp1 --description "MVP1 retrieval foundation"
gh label create mvp2 --description "MVP2 grounded LLM answers"
gh label create mvp3 --description "MVP3 production readiness"
gh label create architecture --description "Architecture and design docs"
gh label create documentation --description "Documentation work"
gh label create feature --description "Product or engineering feature"
gh label create testing --description "Tests, smoke checks, and QA"
gh label create ingestion --description "Document ingestion and extraction"
gh label create retrieval --description "Vector search and retrieval"
gh label create reranking --description "Reranking retrieved chunks"
gh label create llm --description "LLM answer generation"
gh label create api --description "API work"
gh label create frontend --description "UI work"
gh label create configuration --description "Environment and provider setup"
gh label create mongodb --description "MongoDB and vector index work"
gh label create template --description "Reusable project templates"
gh label create repository --description "Repository publishing and hygiene"
gh label create evaluation --description "Answer and retrieval quality checks"
```

## 2. Create Milestones

```powershell
gh milestone create "MVP1 - Retrieval Foundation" --description "Document extraction, chunking, embeddings, MongoDB Vector Search, local UI/API smoke tests, and documentation."
gh milestone create "MVP2 - FastAPI And Grounded LLM Answers" --description "FastAPI parity, existing-UI acceptance, reranking, LLM answer generation, citations, ask/chat API, and answer UI."
gh milestone create "MVP3 - Profile Agent API And Production Readiness" --description "Hosted profile agent API, portfolio chatbot integration, deployment checks, monitoring, and security posture."
```

## 3. Create Issues

The full issue bodies live in:

- `docs/github/issues-mvp1.md`
- `docs/github/issues-mvp2.md`

Fast path:

1. Open GitHub Issues in the browser.
2. Create each issue from the headings in those files.
3. Assign the matching labels and milestone shown below each title.

CLI path:

```powershell
gh issue create --title "Document MVP1 Retrieval Architecture" --label "documentation,architecture,mvp1" --milestone "MVP1 - Retrieval Foundation" --body-file docs/github/issues-mvp1.md
```

For cleaner CLI import, split each issue section into its own body file before running `gh issue create`.

## 4. Create GitHub Project

Project name:

```text
MongoDB RAG Profile Agent
```

Project description:

```text
Build a reproducible document-to-vector-search and grounded-answer system for the Profile Assistant/Profile Agent, moving from MVP1 retrieval foundation to MVP2 reranking/LLM answers and MVP3 hosted portfolio integration.
```

Use `docs/github/project-board.md` for board views and field suggestions.
