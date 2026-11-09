# Portfolio Chat Integration

Status: local browser integration is implemented; live answer/citation acceptance and
deployment remain pending. The portfolio checks FastAPI `GET /api/status` before
`POST /api/ask`. The keyword matcher supplies the relevant section link, but its
answer fallback is temporarily disabled during latency troubleshooting. The deployed
endpoint remains commented out until preview acceptance. See
`project-status.md` for the current handoff and
`templates/document-vector-pipeline/PIPELINE_AUDIT.md` for the chronological record.

## Request Contract

The static portfolio first calls GET `/api/status` to verify MongoDB and the configured
chat model, then sends the visitor's question to the configured RAG API base URL at
POST `/api/ask` with JSON fields `query`, `top_k: 3`, and `min_score`. The portfolio
requires the response model to be `gpt-5.5`. Local browser testing serves the
portfolio from `http://127.0.0.1:5500` and runs the profile API on port `8766`.
Configure `CORS_ALLOWED_ORIGINS` with the exact portfolio origins. The API base URL
is public configuration, not a secret.

Never include a MongoDB URI, model API key, or shared secret in HTML/JavaScript. Do not pass database or collection overrides from the browser. The deployed API must restrict this route to the reviewed public profile collection.

Successful responses contain answer, citations, insufficient_evidence, and
`timings_ms` for embedding, retrieval, reranking, model generation, and total API
time. Keep answers direct and brief; show resolved evidence IDs, source/title/section,
chunk IDs, and vector/rerank scores only in an opt-in collapsed disclosure. Avoid
exposing raw diagnostics to visitors.

## LLM Answer Acceptance

The website needs the grounded LLM response from /api/ask, not just retrieved or
reranked chunks. Configure CHAT_PROVIDER and CHAT_MODEL on the backend and keep its
API key server-side. Voyage is used for embeddings/reranking; it is not a generative
chat model. The adapter supports OpenAI, Anthropic, xAI/Grok, and DeepSeek when the
corresponding optional package and provider credentials are installed.

Before connecting the website, invoke /api/ask with the intended provider and verify:

- A question requiring facts from more than one retrieved chunk receives a useful,
  concise synthesis grounded only in those chunks.
- Inline evidence markers match the returned citation IDs and resolve to the exact
  source_id/chunk_id/title/section supplied as evidence.
- No-match questions return insufficient_evidence with no citations.
- Invalid model output and provider/network errors return a controlled API error;
  the browser displays a retryable message and does not expose exception details.
- At least one real invocation is recorded for every provider described as tested.
  An adapter import or key-presence diagnostic alone is not provider verification.

## Website Behavior

- Show loading and prevent duplicate submission while a request is in flight.
- Support Enter submission and preserve keyboard/accessibility behavior.
- Keep the answer concise and focused on the visitor's question.
- Put evidence details and scores in a collapsed, keyboard-accessible disclosure.
- Check `/api/status` before `/api/ask` and display measured timings for diagnosis.
- Keep local keyword fallback disabled during API latency troubleshooting so failures
  remain visible.
- For insufficient evidence, show the cautious answer and no invented citations.
- On timeout, network, provider, or malformed-response errors, show the API error and
  elapsed time; do not substitute a local answer while troubleshooting.
- If local keyword fallback is used, label it as a local answer; never present it as RAG output.
- Send only the question and supported retrieval options. Do not silently persist visitor questions.

## Deployment Boundary

Deploy MongoDB RAG as a separate Vercel project rooted at the RAG repository, using its existing api/index.py, pyproject.toml, and vercel.json. Deploy the static portfolio independently. Point portfolio preview to API preview; production points to production API.

Set MongoDB, embedding, reranker, and chat-provider secrets in the RAG Vercel project's server-side environment settings. Keep them out of portfolio code and browser bundles.

FastAPI CORS middleware reads `CORS_ALLOWED_ORIGINS`; local defaults allow only the
two localhost port-5500 origins. Before browser calls to a preview or production API,
set the exact deployed portfolio origins in that server-side variable. CORS controls
browser access but is not authentication: also enforce request/time limits, rate/abuse
controls, and a server-side database target allowlist. Do not embed a static API token
in public JavaScript.

The current vercel.json excludes development files. It is not itself a deployment, secret-management, CORS, or auth configuration. Measure /api/ask duration in preview before setting a function-duration override.

## Acceptance Gates

1. Local API: real configured chat-model invocation; multi-chunk synthesis; valid citations; insufficient evidence; malformed output; provider error.
2. Vercel preview: status, MongoDB access, search/rerank/ask, citation shape, timeout, bundle size, and function duration.
3. Browser preview: CORS, answer, citations, no-context response, visible offline/API errors, keyboard, and mobile layout.
4. Production: confirm exact origins and environment values, then repeat essential answer/citation/error checks.

Do not mark website chat complete until preview and production results are recorded in the portfolio roadmap and RAG audit.
