# Corpus Explorer — Design Spec

**Date:** 2026-04-27
**Branch:** `feat/corpus-explorer`
**Status:** Approved, ready for implementation planning

---

## Context

Klippy extracts keywords from indexed documents during ingestion (`KeywordExtractor`, 5 keywords per node, stored as `excerpt_keywords` in Qdrant metadata). This data exists but is only surfaced via a random-sample `/keywords` endpoint used for chat placeholder chips.

The goal is to build a proper **Corpus Explorer** — a read-only analytics dashboard at `/explore` that lets users understand what knowledge exists in their indexed corpus: which topics appear most, how content is distributed across sources (ClickUp vs GitHub) and types (task, doc, issue, readme), and basic coverage stats.

A secondary note: **agentic RAG** was considered but deferred. The current query use cases (project status checks, task lookups) are well-served by the existing retrieval pipeline. Revisit when cross-source multi-hop queries become a real need.

---

## Architecture

A single new SvelteKit route (`/explore`) backed by a single new FastAPI endpoint (`GET /corpus/stats`). The page is stateless — no user input, no stores. Data is fetched once at page load via a `+page.ts` load function and rendered as a dashboard.

The `/corpus/stats` endpoint aggregates Qdrant metadata server-side and caches the result in Redis (1-hour TTL, matching the existing `/questions` and `/keywords` pattern).

---

## Backend: `GET /corpus/stats`

### Endpoint

```
GET /corpus/stats
```

### Response

```json
{
  "overview": {
    "total_nodes": 1420,
    "sources": ["ClickUp", "GitHub"],
    "last_ingested": "2026-04-25T14:32:00Z",
    "date_range": { "from": "2024-01-01", "to": "2026-04-25" }
  },
  "keywords": {
    "top": [
      { "keyword": "Machine Learning", "count": 43 },
      { "keyword": "RAG", "count": 37 }
    ]
  },
  "by_source": {
    "ClickUp": {
      "nodes": 820,
      "top_keywords": ["sprint", "task", "review"]
    },
    "GitHub": {
      "nodes": 600,
      "top_keywords": ["README", "API", "schema"]
    }
  },
  "by_type": {
    "task": 500,
    "doc": 320,
    "issue": 200,
    "readme": 100
  }
}
```

Returns `200` with empty/zero values if no nodes are indexed. Returns `503` if Qdrant is unreachable.

### Implementation

- Use Qdrant `scroll` to paginate through the full collection, extracting `excerpt_keywords`, `source`, `type`, and `last_modified_date` from each point's payload.
- Parse comma-separated keyword strings, lowercase, strip whitespace, count occurrences globally and per-source.
- Sort keywords by count descending; return top 30 globally, top 5 per source.
- `last_ingested` = max `last_modified_date` across all nodes.
- `date_range` = min/max `last_modified_date`.
- Cache result in Redis with key `corpus_stats` and 1-hour TTL (same pattern as `_get_cached_questions` in `main.py`).

### Files to modify

- `backend/main.py` — add `GET /corpus/stats` route
- `backend/tests/test_api.py` — add tests for the new endpoint

---

## Frontend: `/explore` route

### New files

- `frontend/src/routes/explore/+page.svelte`
- `frontend/src/routes/explore/+page.ts` (load function)

### Layout

Four sections, stacked on mobile, 2-column grid on desktop (≥768px):

#### 1. Overview cards
Four stat chips in a row:
- **Total Nodes** — `overview.total_nodes`
- **Sources** — comma-joined `overview.sources`
- **Last Ingested** — relative time (e.g. "2 days ago")
- **Date Range** — `from` → `to`

#### 2. Top Keywords
Horizontal frequency bars — pure CSS (`div` widths proportional to max count). Top 30 keywords. Each bar label is the keyword; a small count badge sits at the right end. No chart library.

#### 3. By Source
One row per source: source name, node count, percentage of total (as a filled progress bar), and a `+` toggle to reveal that source's top 5 keywords inline.

#### 4. By Type
Same progress-bar layout as source, one row per type (task, doc, issue, readme).

### Sidebar entry

Add an "Explore" nav link to `frontend/src/routes/chats/+layout.svelte` using the `Map` icon from lucide-svelte, positioned below the chat list.

### States

- **Loading** — skeleton placeholders for each section while fetch is in-flight.
- **Empty corpus** — message explaining keywords are generated during ingestion with `--extract-keywords`; link to docs or the ingest API.
- **Error** — banner if `/corpus/stats` returns an error.

### Files to modify

- `frontend/src/routes/chats/+layout.svelte` — add Explore nav link
- New: `frontend/src/routes/explore/+page.svelte`
- New: `frontend/src/routes/explore/+page.ts`
- `frontend/src/routes/explore/*.test.ts` — Vitest unit tests for data transforms

---

## Data Flow

```
Page load
  → +page.ts load()
  → GET /corpus/stats
  → backend/main.py handler
    → Redis cache hit? → return cached
    → Qdrant scroll (all nodes)
    → aggregate keywords, source, type, dates
    → cache in Redis (1h)
    → return JSON
  → Svelte components render sections
```

---

## Error Handling

| Scenario | Backend | Frontend |
|---|---|---|
| Collection empty | 200 with zeros/empty arrays | Show "empty corpus" state |
| `excerpt_keywords` not populated | 200, keywords array empty | Show hint about `--extract-keywords` |
| Qdrant unreachable | 503 | Error banner |
| Redis unreachable | Skip cache, return live data | Transparent to user |

---

## Testing

### Backend
- Unit: keyword aggregation (comma-separated parse, count, sort, top-N)
- Unit: empty collection → all zeros
- Integration (mock Qdrant): `/corpus/stats` response shape matches schema
- Integration: Redis caching behaviour (second call hits cache)

### Frontend
- Vitest unit: data transformation from raw API response to chart-ready arrays
- Playwright e2e: `/explore` renders, displays at least one keyword chip, stat cards show non-zero values (requires seeded data)

---

## Out of Scope (this iteration)

- Keyword → chat navigation (clicking a keyword starts a pre-filled chat)
- Agentic RAG / automatic source routing
- Keyword frequency over time / trend charts
- Per-keyword drill-down to source documents
