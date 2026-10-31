param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Run-Gh {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$GhArgs)
    if ($DryRun) {
        Write-Host "gh $($GhArgs -join ' ')"
        return
    }
    & gh @GhArgs
}

function Ensure-Label {
    param(
        [string]$Name,
        [string]$Description
    )
    $existing = if ($DryRun) { "" } else { gh label list --search $Name --json name --jq '.[].name' }
    if ($existing -contains $Name) {
        Write-Host "Label exists: $Name"
        return
    }
    Run-Gh @("label", "create", $Name, "--description", $Description)
}

function Ensure-Milestone {
    param(
        [string]$Title,
        [string]$Description
    )
    $existing = if ($DryRun) { "" } else { gh milestone list --state all --json title --jq '.[].title' }
    if ($existing -contains $Title) {
        Write-Host "Milestone exists: $Title"
        return
    }
    Run-Gh @("milestone", "create", $Title, "--description", $Description)
}

function Create-Issue {
    param(
        [string]$Title,
        [string]$Labels,
        [string]$Milestone,
        [string]$Body
    )
    $tmp = New-TemporaryFile
    Set-Content -LiteralPath $tmp -Value $Body
    try {
        Run-Gh @(
            "issue",
            "create",
            "--title",
            $Title,
            "--label",
            $Labels,
            "--milestone",
            $Milestone,
            "--body-file",
            $tmp
        )
    }
    finally {
        Remove-Item -LiteralPath $tmp -Force
    }
}

$labels = @(
    @("mvp", "MVP scoped work"),
    @("mvp1", "MVP1 retrieval foundation"),
    @("mvp2", "MVP2 grounded LLM answers"),
    @("mvp3", "MVP3 production readiness"),
    @("architecture", "Architecture and design docs"),
    @("documentation", "Documentation work"),
    @("feature", "Product or engineering feature"),
    @("testing", "Tests, smoke checks, and QA"),
    @("ingestion", "Document ingestion and extraction"),
    @("retrieval", "Vector search and retrieval"),
    @("reranking", "Reranking retrieved chunks"),
    @("llm", "LLM answer generation"),
    @("api", "API work"),
    @("frontend", "UI work"),
    @("configuration", "Environment and provider setup"),
    @("mongodb", "MongoDB and vector index work"),
    @("template", "Reusable project templates"),
    @("repository", "Repository publishing and hygiene"),
    @("evaluation", "Answer and retrieval quality checks")
)

foreach ($label in $labels) {
    Ensure-Label -Name $label[0] -Description $label[1]
}

Ensure-Milestone `
    -Title "MVP1 - Retrieval Foundation" `
    -Description "Document extraction, chunking, embeddings, MongoDB Vector Search, local UI/API smoke tests, and documentation."

Ensure-Milestone `
    -Title "MVP2 - FastAPI And Grounded LLM Answers" `
    -Description "Reranking, LLM answer generation, citations, ask/chat API, and answer UI."

Ensure-Milestone `
    -Title "MVP3 - Profile Agent API And Production Readiness" `
    -Description "Hosted profile agent API, portfolio chatbot integration, deployment checks, monitoring, and security posture."

$issues = @(
    @{
        Title = "Document MVP1 Retrieval Architecture"
        Labels = "documentation,architecture,mvp1"
        Milestone = "MVP1 - Retrieval Foundation"
        Body = @"
## Description

Create a clear MVP1 architecture document showing how documents move through extraction, chunking, embeddings, MongoDB storage, vector search, and UI retrieval.

## Acceptance Criteria

- [ ] Architecture doc exists under docs/architecture/.
- [ ] MVP1 boundaries are explicit.
- [ ] API surface is documented.
- [ ] MongoDB record shape is documented.
- [ ] MVP2 handoff points are identified.
"@
    },
    @{
        Title = "Complete MVP1 Document Ingestion Flow"
        Labels = "feature,ingestion,mvp1"
        Milestone = "MVP1 - Retrieval Foundation"
        Body = @"
## Description

Allow users to load a document from drag/drop, file picker, local file path, or pasted text and extract text into the UI for review before chunking.

## Acceptance Criteria

- [ ] Upload extraction endpoint exists.
- [ ] File-path extraction endpoint exists.
- [ ] UI supports drag/drop and file picker.
- [ ] UI supports local file path extraction.
- [ ] Extracted text appears in Document Text.
- [ ] Supported file types are documented.
"@
    },
    @{
        Title = "Verify MVP1 End-To-End Retrieval Baseline"
        Labels = "testing,retrieval,mongodb,mvp1"
        Milestone = "MVP1 - Retrieval Foundation"
        Body = @"
## Description

Verify that reviewed document text can be chunked, embedded with Voyage, stored in MongoDB Atlas Vector Search, and retrieved as ranked chunks.

## Acceptance Criteria

- [ ] Chunk preview works before embedding.
- [ ] Chunk, Embed, and Store inserts chunks into MongoDB.
- [ ] Vector search returns ranked chunks.
- [ ] Smoke test confirms the expected source appears as the top result.
- [ ] Verification is recorded in docs/test-ui-audit.md.
"@
    },
    @{
        Title = "Complete MVP1 Template Package"
        Labels = "documentation,template,mvp1"
        Milestone = "MVP1 - Retrieval Foundation"
        Body = @"
## Description

Update the reusable document-vector pipeline template so future projects can copy the MVP1 setup pattern.

## Acceptance Criteria

- [ ] Template README reflects UI-based document ingestion.
- [ ] Setup checklist includes document extraction and chunk preview.
- [ ] Smoke test commands include test UI routes.
- [ ] Audit template includes extraction, storage, and retrieval evidence fields.
"@
    },
    @{
        Title = "Prepare Repository For GitHub Publishing"
        Labels = "repository,documentation,mvp1"
        Milestone = "MVP1 - Retrieval Foundation"
        Body = @"
## Description

Prepare the project for GitHub by documenting what should be committed and what should remain local.

## Acceptance Criteria

- [ ] README includes publishing notes.
- [ ] .env, virtual environments, caches, and private source documents are excluded.
- [ ] GitHub milestone and issue docs exist.
- [ ] No secrets are included in docs.
"@
    },
    @{
        Title = "Add Reranking Layer After MongoDB Retrieval"
        Labels = "feature,reranking,mvp2"
        Milestone = "MVP2 - FastAPI And Grounded LLM Answers"
        Body = @"
## Description

Retrieve a larger candidate set from MongoDB Vector Search, then rerank the candidates before sending evidence to the LLM.

## Acceptance Criteria

- [ ] Reranker interface exists.
- [ ] Voyage rerank is supported first.
- [ ] Reranking can be toggled on/off.
- [ ] Response includes original vector score and rerank score.
- [ ] Tests cover reranked ordering and fallback behavior.
"@
    },
    @{
        Title = "Add Grounded Answer Generation Endpoint"
        Labels = "feature,llm,api,mvp2"
        Milestone = "MVP2 - FastAPI And Grounded LLM Answers"
        Body = @"
## Description

Add an endpoint that retrieves evidence chunks, selects the best 3-5 chunks, and asks an LLM to produce a concise grounded answer.

## Acceptance Criteria

- [ ] /api/ask or /api/chat endpoint exists.
- [ ] Endpoint accepts a user question and top-k settings.
- [ ] LLM receives only selected evidence chunks.
- [ ] Response includes answer text and citations.
- [ ] No-context behavior is handled gracefully.
"@
    },
    @{
        Title = "Add Citation Mapping And Answer UI"
        Labels = "feature,llm,frontend,mvp2"
        Milestone = "MVP2 - FastAPI And Grounded LLM Answers"
        Body = @"
## Description

Extend the test UI so users can ask a question and view a concise answer, cited chunks, and retrieval diagnostics.

## Acceptance Criteria

- [ ] UI has a clear ask/chat panel.
- [ ] Answer text is visible and concise.
- [ ] Citations include source_id, chunk_id, title, and score fields.
- [ ] Raw retrieval/reranking diagnostics remain available.
"@
    }
)

foreach ($issue in $issues) {
    Create-Issue `
        -Title $issue.Title `
        -Labels $issue.Labels `
        -Milestone $issue.Milestone `
        -Body $issue.Body
}
