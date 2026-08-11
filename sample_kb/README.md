# Northwind Cloud Knowledge Base — RAG Production Practice Set

A fictional B2B payments company's internal knowledge base: 25 documents
across product docs, versioned policies, legal/compliance, engineering
runbooks, support content, pricing, and a changelog. It's built so that
**every production RAG technique in the guide has a real, non-contrived
reason to exist** — nothing here is a toy example.

## Suggested Resume Framing

> "Built a multi-tenant, access-controlled RAG copilot for enterprise
> support & compliance queries — hybrid dense+sparse retrieval, corrective
> RAG with self-grading, agentic tool-routing via LangGraph, RAGAS-evaluated
> retrieval pipeline, and full FastAPI production deployment with caching,
> observability, and role-based document filtering."

That's a genuinely differentiated project — most portfolio RAG projects are
"chat with a PDF." This one has multi-tenancy, contradictory/versioned
source data, exact-identifier lookups, and ambiguous/no-answer questions
baked into the source data itself, which is what actually forces you to
build the production techniques rather than skip them.

## Directory Structure & Metadata

Every file has YAML frontmatter — parse it into `Document.metadata` at
ingestion time. Fields used throughout:

| Field | Purpose |
|---|---|
| `doc_id` | stable ID for incremental re-indexing |
| `team` | owning team |
| `access_control` | comma-separated list of roles allowed to retrieve this doc — **this is your multi-tenancy field** |
| `content_type` | prose / reference / faq / policy / runbook / postmortem / ticket_transcript / changelog |
| `updated_at` | recency, staleness detection |
| `status` / `superseded_by` / `supersedes` | version-chain tracking (see the refund policy pair) |
| `confidentiality` | `internal` docs should never appear in a public-facing demo |

## Exercise Map — Which File(s) Test Which Technique

### 1. Chunking strategies (§4.2)
- `product/api-reference-payments.md`, `pricing/pricing-plans.md` — tables;
  practice **not** naively splitting mid-table.
- `engineering/postmortem-2026-03-14-checkout-outage.md` — has a timeline
  list, a root-cause section, and numbered action items; good test of
  whether header-aware splitting keeps each section coherent.
- `support/support-ticket-transcript-*.md` — conversational, turn-by-turn
  text; a fixed-size splitter will happily cut a customer's sentence in half
  here. Try recursive vs. semantic chunking on these specifically and
  compare.

### 2. Metadata filtering / multi-tenancy (§4.5)
- Everything under `compliance/` and `engineering/` has restrictive
  `access_control`. **Exercise:** build two retrievers — one for a
  `support` role, one for an `engineering` role — and confirm the support
  role can never retrieve `soc2-compliance-summary.md` or
  `runbook-payment-service-outage.md`, even if a user explicitly asks about
  them. This is the access-control-at-query-time pattern from §4.5/§9.3 —
  filter, don't just avoid displaying.

### 3. Hybrid search / BM25 (§5.2)
- `engineering/error-code-reference.md` and every runbook contain exact
  codes (`ERR-4092`, `ADDON-SSO-001`, `JIRA-SEC-4471`). **Exercise:** ask
  "what does ERR-4092 mean" against pure dense retrieval vs. hybrid — dense
  retrieval alone frequently fails on short exact-identifier queries because
  the semantic content of "ERR-4092" is thin. This is the clearest possible
  demonstration of why hybrid search exists, and a great chart for your
  resume project write-up.

### 4. Staleness / contradiction / corrective RAG (§7.2)
- `policies/refund-policy-v1-deprecated.md` vs
  `policies/refund-policy-v2-current.md` are near-duplicates with
  **different numbers** (14 vs 30 day window, 10 vs 5-7 day processing).
  **Exercise:** without any handling, plain retrieval will sometimes return
  the deprecated doc and the model will confidently quote the wrong refund
  window. Build the corrective-RAG grading step to prefer `status: current`
  and demonstrate the before/after with RAGAS faithfulness scores.

### 5. "No answer exists" handling
- Deliberately unanswerable questions to add to your eval set: *"What's your
  refund policy for APAC customers?"* (unsupported region, per
  `product-overview.md`), *"What SLA credit do I get on the free plan?"*
  (Starter has none), *"Can I use the API without authentication?"* (no —
  but make sure the model doesn't invent a workaround). These are exactly
  the queries that expose whether your prompt's "say I don't know" rule
  (§6.1) actually works, or whether the model hallucinates from
  weakly-related chunks.

### 6. MMR / redundancy handling (§5.1)
- `pricing/pricing-plans.md`, `pricing/enterprise-addons-catalog.md`, and
  `product/product-overview.md` all mention plan tiers and pricing with
  overlapping content. Plain top-k similarity search on a pricing question
  can return 4 chunks that are all slight rephrasings of the same table —
  MMR should visibly do better here.

### 7. Agentic RAG / tool routing (§7.1)
- Mix retrieval-needed questions ("what's the SLA for Enterprise") with
  non-retrieval turns ("thanks, that's all" / "hi") in a conversation and
  confirm the agent only calls the retriever tool when actually needed,
  instead of always retrieving.

### 8. Reranking (§5.4)
- Ask a specific question like *"What happens to queued webhook events if my
  endpoint is down for 6 hours?"* — the answer is split across
  `api-reference-webhooks.md` (retry schedule) and
  `support-ticket-transcript-002.md` (a concrete real example of exactly
  this happening). A reranker should surface both above less-relevant
  tangential matches; measure `top_n=4` with and without reranking.

### 9. Citations (§6.4)
- Every doc has a stable `doc_id` — use it as your citation key so you can
  programmatically verify the model's cited sources actually appear in the
  retrieved set, per the `CitedAnswer` structured-output pattern.

### 10. Evaluation (Part E)
- `eval/golden_set.jsonl` in this bundle has starter (question, doc_id,
  notes) rows spanning all the categories above — extend it to 50-100 rows
  as your actual eval set before you start tuning anything.

## What to Build, in Order

1. Ingest all 25 docs with full metadata (§4.1-4.5).
2. Plain LCEL RAG chain, dense retrieval only (§6.2) — get a baseline.
3. Run the golden eval set through RAGAS (Part E) and **write down the
   baseline scores** — this before/after comparison is what makes your
   resume project credible instead of just a list of buzzwords.
4. Add hybrid search (§5.2) — re-run eval, note the delta on the
   exact-identifier questions specifically.
5. Add reranking (§5.4) — re-run eval.
6. Add the access-control filter (§4.5/§9.3) — write a specific test
   proving cross-tenant leakage is blocked, not just "looks fine."
7. Add corrective RAG grading (§7.2) to handle the refund-policy-version
   contradiction — re-run eval, this should visibly move faithfulness.
8. Wrap it as an agent with `create_agent` (§7.1) for multi-turn chat.
9. Deploy behind FastAPI with caching + LangSmith tracing (Part F).
10. Write up the before/after RAGAS numbers for each step — **that table is
    your resume/portfolio artifact**, not just the code.
