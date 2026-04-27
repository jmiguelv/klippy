# Corpus Explorer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a read-only `/explore` dashboard backed by `GET /corpus/stats` that aggregates keyword, source, type, and date metadata from all indexed Qdrant nodes and caches results in Redis.

**Architecture:** A pure aggregation helper (`_aggregate_corpus_stats`) is unit-tested in isolation, then wired into a FastAPI endpoint that scrolls the full Qdrant collection and caches the result for 1 hour. On the frontend, a SvelteKit `+page.ts` load function returns a deferred Promise so the page can render skeleton placeholders while the fetch is in-flight. Four dashboard sections are rendered from pure transform functions that live in `src/lib/corpus-stats.ts`.

**Tech Stack:** Python 3.12, FastAPI, Qdrant client, Redis, SvelteKit 2, Svelte 5 (`$state`/`$props`/`$derived`), TypeScript, Vitest, `@testing-library/svelte`, lucide-svelte

---

## File Structure

**Modified:**
- `backend/main.py` — add `_extract_payload_field`, `_aggregate_corpus_stats`, and `GET /corpus/stats`
- `backend/tests/test_api.py` — add corpus stats unit + integration tests (update import block)
- `frontend/src/routes/chats/+layout.svelte` — add Explore sidebar nav link with `Map` icon

**Created:**
- `frontend/src/lib/corpus-stats.ts` — `CorpusStats` types + `toRelativeTime`, `toBarWidth`, `toSortedEntries`, `sortedSourceEntries`
- `frontend/src/lib/corpus-stats.test.ts` — Vitest unit tests for all transform functions
- `frontend/src/routes/explore/+page.ts` — deferred-fetch load function
- `frontend/src/routes/explore/explore.test.ts` — Vitest unit tests for the load function
- `frontend/src/routes/explore/+page.svelte` — dashboard UI

---

## Task 1: Backend — `_extract_payload_field` + `_aggregate_corpus_stats` helpers

**Files:**
- Modify: `backend/tests/test_api.py`
- Modify: `backend/main.py`

- [ ] **Step 1: Update the test import block to include new functions**

In `backend/tests/test_api.py`, change:
```python
with patch("qdrant_client.QdrantClient"), \
     patch("qdrant_client.AsyncQdrantClient"), \
     patch("redis.Redis"), \
     patch("engine.IngestionCache"), \
     patch("engine.RedisCache"):
    from main import app, engine
```
to:
```python
with patch("qdrant_client.QdrantClient"), \
     patch("qdrant_client.AsyncQdrantClient"), \
     patch("redis.Redis"), \
     patch("engine.IngestionCache"), \
     patch("engine.RedisCache"):
    from main import app, engine, redis_client, _extract_payload_field, _aggregate_corpus_stats
```

- [ ] **Step 2: Write failing unit tests for the helper functions**

Append to `backend/tests/test_api.py`:

```python
# ── _extract_payload_field ────────────────────────────────────────────────────

def test_extract_payload_field_top_level():
    assert _extract_payload_field({"source": "GitHub"}, "source") == "GitHub"

def test_extract_payload_field_node_content():
    payload = {"_node_content": json.dumps({"metadata": {"source": "ClickUp"}})}
    assert _extract_payload_field(payload, "source") == "ClickUp"

def test_extract_payload_field_top_level_takes_precedence():
    payload = {
        "source": "TopLevel",
        "_node_content": json.dumps({"metadata": {"source": "Nested"}}),
    }
    assert _extract_payload_field(payload, "source") == "TopLevel"

def test_extract_payload_field_missing_returns_none():
    assert _extract_payload_field({}, "source") is None
    assert _extract_payload_field({"_node_content": json.dumps({"metadata": {}})}, "source") is None

def test_extract_payload_field_invalid_json_returns_none():
    assert _extract_payload_field({"_node_content": "not-json"}, "source") is None


# ── _aggregate_corpus_stats ───────────────────────────────────────────────────

def test_aggregate_corpus_stats_empty():
    result = _aggregate_corpus_stats([])
    assert result["overview"]["total_nodes"] == 0
    assert result["overview"]["sources"] == []
    assert result["overview"]["last_ingested"] is None
    assert result["overview"]["date_range"] == {"from": None, "to": None}
    assert result["keywords"]["top"] == []
    assert result["by_source"] == {}
    assert result["by_type"] == {}


def _make_point(payload: dict):
    pt = MagicMock()
    pt.payload = payload
    return pt


def test_aggregate_corpus_stats_keyword_counting_string():
    pt = _make_point({
        "excerpt_keywords": "ai, machine learning, ai",
        "source": "GitHub",
        "type": "readme",
        "last_modified_date": "2026-01-01",
    })
    result = _aggregate_corpus_stats([pt])
    kw_map = {kw["keyword"]: kw["count"] for kw in result["keywords"]["top"]}
    assert kw_map["Ai"] == 2
    assert kw_map["Machine Learning"] == 1


def test_aggregate_corpus_stats_keyword_counting_list():
    pt = _make_point({
        "excerpt_keywords": ["rag", "llm", "rag"],
        "source": "GitHub",
    })
    result = _aggregate_corpus_stats([pt])
    kw_map = {kw["keyword"]: kw["count"] for kw in result["keywords"]["top"]}
    assert kw_map["Rag"] == 2
    assert kw_map["Llm"] == 1


def test_aggregate_corpus_stats_source_and_type_breakdown():
    pts = [
        _make_point({"source": "ClickUp", "type": "task", "last_modified_date": "2026-01-01", "excerpt_keywords": ""}),
        _make_point({"source": "GitHub",  "type": "readme", "last_modified_date": "2026-02-01", "excerpt_keywords": ""}),
        _make_point({"source": "ClickUp", "type": "doc", "last_modified_date": "2026-03-01", "excerpt_keywords": ""}),
    ]
    result = _aggregate_corpus_stats(pts)
    assert result["overview"]["total_nodes"] == 3
    assert result["by_source"]["ClickUp"]["nodes"] == 2
    assert result["by_source"]["GitHub"]["nodes"] == 1
    assert result["by_type"]["task"] == 1
    assert result["by_type"]["readme"] == 1
    assert result["by_type"]["doc"] == 1
    assert result["overview"]["date_range"]["from"] == "2026-01-01"
    assert result["overview"]["date_range"]["to"] == "2026-03-01"
    assert result["overview"]["last_ingested"] == "2026-03-01"


def test_aggregate_corpus_stats_top_30_keywords_global():
    kws = ", ".join(f"kw{i}" for i in range(35))
    pt = _make_point({"excerpt_keywords": kws, "source": "X"})
    result = _aggregate_corpus_stats([pt])
    assert len(result["keywords"]["top"]) == 30


def test_aggregate_corpus_stats_top_5_keywords_per_source():
    kws = ", ".join(f"kw{i}" for i in range(10))
    pt = _make_point({"excerpt_keywords": kws, "source": "GitHub"})
    result = _aggregate_corpus_stats([pt])
    assert len(result["by_source"]["GitHub"]["top_keywords"]) == 5


def test_aggregate_corpus_stats_keyword_title_case():
    pt = _make_point({"excerpt_keywords": "machine learning", "source": "X"})
    result = _aggregate_corpus_stats([pt])
    assert result["keywords"]["top"][0]["keyword"] == "Machine Learning"
    assert result["by_source"]["X"]["top_keywords"] == ["Machine Learning"]
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_api.py -k "extract_payload_field or aggregate_corpus_stats" -v 2>&1 | tail -20
```

Expected: `ImportError: cannot import name '_extract_payload_field'`

- [ ] **Step 4: Implement helpers in `backend/main.py`**

Add after the `_INTERNAL_FIELDS` block (after line 255) in `backend/main.py`:

```python
def _extract_payload_field(payload: dict, field: str):
    """Returns field value from top-level payload or from _node_content metadata."""
    if field in payload:
        return payload[field]
    if "_node_content" in payload:
        try:
            return json.loads(payload["_node_content"]).get("metadata", {}).get(field)
        except (json.JSONDecodeError, TypeError):
            pass
    return None


def _aggregate_corpus_stats(points: list) -> dict:
    """Aggregates keyword/source/type/date stats from a list of Qdrant points."""
    keyword_counts: Counter = Counter()
    source_keyword_counts: dict[str, Counter] = defaultdict(Counter)
    source_counts: Counter = Counter()
    type_counts: Counter = Counter()
    dates: list[str] = []

    for point in points:
        payload = point.payload or {}

        source = str(_extract_payload_field(payload, "source") or "unknown")
        doc_type = _extract_payload_field(payload, "type")
        last_modified = _extract_payload_field(payload, "last_modified_date")
        raw_keywords = _extract_payload_field(payload, "excerpt_keywords")

        source_counts[source] += 1
        if doc_type is not None:
            type_counts[str(doc_type)] += 1
        if last_modified is not None:
            dates.append(str(last_modified))

        if raw_keywords:
            if isinstance(raw_keywords, str):
                kws = [k.strip().lower() for k in raw_keywords.split(",") if k.strip()]
            elif isinstance(raw_keywords, list):
                kws = [str(k).strip().lower() for k in raw_keywords if str(k).strip()]
            else:
                kws = []
            for kw in kws:
                keyword_counts[kw] += 1
                source_keyword_counts[source][kw] += 1

    total = sum(source_counts.values())
    sorted_dates = sorted(dates)

    return {
        "overview": {
            "total_nodes": total,
            "sources": list(source_counts.keys()),
            "last_ingested": sorted_dates[-1] if sorted_dates else None,
            "date_range": {
                "from": sorted_dates[0] if sorted_dates else None,
                "to": sorted_dates[-1] if sorted_dates else None,
            },
        },
        "keywords": {
            "top": [
                {"keyword": kw.title(), "count": cnt}
                for kw, cnt in keyword_counts.most_common(30)
            ]
        },
        "by_source": {
            src: {
                "nodes": cnt,
                "top_keywords": [kw.title() for kw, _ in source_keyword_counts[src].most_common(5)],
            }
            for src, cnt in source_counts.items()
        },
        "by_type": dict(type_counts),
    }
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_api.py -k "extract_payload_field or aggregate_corpus_stats" -v 2>&1 | tail -20
```

Expected: all 12 new tests PASSED

- [ ] **Step 6: Commit**

```bash
git add backend/main.py backend/tests/test_api.py
git commit -m "feat(corpus): add _aggregate_corpus_stats helper with unit tests"
```

---

## Task 2: Backend — `GET /corpus/stats` endpoint

**Files:**
- Modify: `backend/tests/test_api.py`
- Modify: `backend/main.py`

- [ ] **Step 1: Write failing integration tests**

Append to `backend/tests/test_api.py`:

```python
# ── GET /corpus/stats ─────────────────────────────────────────────────────────

def test_get_corpus_stats_empty_collection(mocker):
    mocker.patch.object(engine.client, "scroll", return_value=([], None))
    mocker.patch.object(redis_client, "get", return_value=None)
    mocker.patch.object(redis_client, "setex")

    response = client.get("/corpus/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["overview"]["total_nodes"] == 0
    assert data["keywords"]["top"] == []
    assert data["by_source"] == {}
    assert data["by_type"] == {}


def test_get_corpus_stats_with_data(mocker):
    pt = MagicMock()
    pt.payload = {
        "excerpt_keywords": "rag, llm",
        "source": "GitHub",
        "type": "readme",
        "last_modified_date": "2026-01-15",
    }
    mocker.patch.object(engine.client, "scroll", return_value=([pt], None))
    mocker.patch.object(redis_client, "get", return_value=None)
    mocker.patch.object(redis_client, "setex")

    response = client.get("/corpus/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["overview"]["total_nodes"] == 1
    assert "GitHub" in data["overview"]["sources"]
    assert any(kw["keyword"] == "Rag" for kw in data["keywords"]["top"])


def test_get_corpus_stats_redis_cache_hit(mocker):
    cached_payload = {
        "overview": {"total_nodes": 99, "sources": ["X"], "last_ingested": None, "date_range": {"from": None, "to": None}},
        "keywords": {"top": []},
        "by_source": {},
        "by_type": {},
    }
    mocker.patch.object(redis_client, "get", return_value=json.dumps(cached_payload))
    scroll_mock = mocker.patch.object(engine.client, "scroll")

    response = client.get("/corpus/stats")
    assert response.status_code == 200
    assert response.json()["overview"]["total_nodes"] == 99
    scroll_mock.assert_not_called()


def test_get_corpus_stats_caches_result(mocker):
    mocker.patch.object(engine.client, "scroll", return_value=([], None))
    mocker.patch.object(redis_client, "get", return_value=None)
    setex_mock = mocker.patch.object(redis_client, "setex")

    client.get("/corpus/stats")
    setex_mock.assert_called_once()
    args = setex_mock.call_args[0]
    assert args[0] == "corpus_stats"
    assert args[1] == 3600


def test_get_corpus_stats_qdrant_unreachable(mocker):
    mocker.patch.object(redis_client, "get", return_value=None)
    mocker.patch.object(engine.client, "scroll", side_effect=Exception("connection refused"))

    response = client.get("/corpus/stats")
    assert response.status_code == 503
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_api.py -k "get_corpus_stats" -v 2>&1 | tail -20
```

Expected: `FAILED` — `404 Not Found` (endpoint does not exist yet)

- [ ] **Step 3: Implement `GET /corpus/stats` in `backend/main.py`**

Add after the `_aggregate_corpus_stats` function:

```python
CORPUS_STATS_CACHE_KEY = "corpus_stats"


@app.get("/corpus/stats")
async def get_corpus_stats():
    cached = redis_client.get(CORPUS_STATS_CACHE_KEY)
    if cached:
        return json.loads(cached)

    try:
        all_points = []
        offset = None
        while True:
            result, offset = engine.client.scroll(
                collection_name=engine.collection_name,
                limit=1000,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            all_points.extend(result)
            if offset is None:
                break

        stats = _aggregate_corpus_stats(all_points)
        redis_client.setex(CORPUS_STATS_CACHE_KEY, STATS_CACHE_TTL, json.dumps(stats))
        return stats
    except Exception as e:
        logger.error(f"Error fetching corpus stats: {e}")
        raise HTTPException(status_code=503, detail="Qdrant unreachable")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_api.py -k "get_corpus_stats" -v 2>&1 | tail -20
```

Expected: all 5 new tests PASSED

- [ ] **Step 5: Run the full test suite to confirm no regressions**

```bash
cd backend && python -m pytest tests/test_api.py -v 2>&1 | tail -10
```

Expected: all tests PASSED

- [ ] **Step 6: Commit**

```bash
git add backend/main.py backend/tests/test_api.py
git commit -m "feat(corpus): add GET /corpus/stats endpoint with Redis cache"
```

---

## Task 3: Frontend — corpus-stats transform functions

**Files:**
- Create: `frontend/src/lib/corpus-stats.ts`
- Create: `frontend/src/lib/corpus-stats.test.ts`

- [ ] **Step 1: Write failing tests**

Create `frontend/src/lib/corpus-stats.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
    toRelativeTime,
    toBarWidth,
    toSortedEntries,
    sortedSourceEntries,
} from './corpus-stats';

describe('toRelativeTime', () => {
    beforeEach(() => {
        vi.useFakeTimers();
        vi.setSystemTime(new Date('2026-04-27T12:00:00Z'));
    });

    afterEach(() => {
        vi.useRealTimers();
    });

    it('toRelativeTime_null_returnsDash', () => {
        expect(toRelativeTime(null)).toBe('—');
    });

    it('toRelativeTime_today_returnsToday', () => {
        expect(toRelativeTime('2026-04-27')).toBe('today');
    });

    it('toRelativeTime_yesterday_returnsYesterday', () => {
        expect(toRelativeTime('2026-04-26')).toBe('yesterday');
    });

    it('toRelativeTime_sevenDaysAgo_returnsDaysAgo', () => {
        expect(toRelativeTime('2026-04-20')).toBe('7 days ago');
    });

    it('toRelativeTime_thirtyFiveDaysAgo_returnsMonthAgo', () => {
        expect(toRelativeTime('2026-03-23')).toBe('1 month ago');
    });

    it('toRelativeTime_fourHundredDaysAgo_returnsYearAgo', () => {
        expect(toRelativeTime('2025-03-23')).toBe('1 year ago');
    });

    it('toRelativeTime_invalidString_returnsInputString', () => {
        expect(toRelativeTime('not-a-date')).toBe('not-a-date');
    });
});

describe('toBarWidth', () => {
    it('toBarWidth_zeroMax_returnsZeroPercent', () => {
        expect(toBarWidth(5, 0)).toBe('0%');
    });

    it('toBarWidth_equalToMax_returns100Percent', () => {
        expect(toBarWidth(10, 10)).toBe('100%');
    });

    it('toBarWidth_half_returns50Percent', () => {
        expect(toBarWidth(5, 10)).toBe('50%');
    });

    it('toBarWidth_roundsToNearestPercent', () => {
        expect(toBarWidth(1, 3)).toBe('33%');
    });
});

describe('toSortedEntries', () => {
    it('toSortedEntries_sortsDescending', () => {
        const result = toSortedEntries({ task: 500, doc: 320, issue: 200 });
        expect(result).toEqual([['task', 500], ['doc', 320], ['issue', 200]]);
    });

    it('toSortedEntries_emptyObject_returnsEmpty', () => {
        expect(toSortedEntries({})).toEqual([]);
    });
});

describe('sortedSourceEntries', () => {
    it('sortedSourceEntries_sortsByNodeCountDescending', () => {
        const result = sortedSourceEntries({
            GitHub: { nodes: 300, top_keywords: [] },
            ClickUp: { nodes: 700, top_keywords: [] },
        });
        expect(result[0][0]).toBe('ClickUp');
        expect(result[1][0]).toBe('GitHub');
    });
});
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd frontend && npx vitest run src/lib/corpus-stats.test.ts 2>&1 | tail -10
```

Expected: `Cannot find module './corpus-stats'`

- [ ] **Step 3: Implement `frontend/src/lib/corpus-stats.ts`**

```typescript
export interface KeywordCount {
    keyword: string;
    count: number;
}

export interface SourceStats {
    nodes: number;
    top_keywords: string[];
}

export interface CorpusStats {
    overview: {
        total_nodes: number;
        sources: string[];
        last_ingested: string | null;
        date_range: { from: string | null; to: string | null };
    };
    keywords: { top: KeywordCount[] };
    by_source: Record<string, SourceStats>;
    by_type: Record<string, number>;
}

export function toRelativeTime(isoString: string | null): string {
    if (!isoString) return '—';
    const then = new Date(isoString).getTime();
    if (isNaN(then)) return isoString;
    const diffMs = Date.now() - then;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    if (diffDays === 0) return 'today';
    if (diffDays === 1) return 'yesterday';
    if (diffDays < 30) return `${diffDays} days ago`;
    const diffMonths = Math.floor(diffDays / 30);
    if (diffMonths < 12) return diffMonths === 1 ? '1 month ago' : `${diffMonths} months ago`;
    const diffYears = Math.floor(diffDays / 365);
    return diffYears === 1 ? '1 year ago' : `${diffYears} years ago`;
}

export function toBarWidth(count: number, maxCount: number): string {
    if (maxCount === 0) return '0%';
    return `${Math.round((count / maxCount) * 100)}%`;
}

export function toSortedEntries(record: Record<string, number>): Array<[string, number]> {
    return Object.entries(record).sort(([, a], [, b]) => b - a);
}

export function sortedSourceEntries(
    bySource: Record<string, SourceStats>
): Array<[string, SourceStats]> {
    return Object.entries(bySource).sort(([, a], [, b]) => b.nodes - a.nodes);
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd frontend && npx vitest run src/lib/corpus-stats.test.ts 2>&1 | tail -10
```

Expected: all 12 tests PASSED

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/corpus-stats.ts frontend/src/lib/corpus-stats.test.ts
git commit -m "feat(corpus): add corpus-stats transform functions with unit tests"
```

---

## Task 4: Frontend — `+page.ts` load function

**Files:**
- Create: `frontend/src/routes/explore/+page.ts`
- Create: `frontend/src/routes/explore/explore.test.ts`

- [ ] **Step 1: Write failing tests**

Create `frontend/src/routes/explore/explore.test.ts`:

```typescript
import { describe, it, expect, vi } from 'vitest';
import { load } from './+page';

vi.mock('$env/static/public', () => ({ PUBLIC_API_URL: 'http://localhost:8000' }));

describe('load', () => {
    it('load_okResponse_statsPromiseResolvesToStats', async () => {
        const mockStats = {
            overview: { total_nodes: 42, sources: ['GitHub'], last_ingested: '2026-01-01', date_range: { from: '2024-01-01', to: '2026-01-01' } },
            keywords: { top: [{ keyword: 'RAG', count: 10 }] },
            by_source: { GitHub: { nodes: 42, top_keywords: ['rag'] } },
            by_type: { readme: 42 },
        };
        const mockFetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => mockStats,
        });

        const result = await load({ fetch: mockFetch } as any);
        const stats = await result.statsPromise;
        expect(stats.overview.total_nodes).toBe(42);
        expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/corpus/stats');
    });

    it('load_errorResponse_statsPromiseRejects', async () => {
        const mockFetch = vi.fn().mockResolvedValue({ ok: false, status: 503 });

        const result = await load({ fetch: mockFetch } as any);
        await expect(result.statsPromise).rejects.toThrow('HTTP 503');
    });
});
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd frontend && npx vitest run src/routes/explore/explore.test.ts 2>&1 | tail -10
```

Expected: `Cannot find module './+page'`

- [ ] **Step 3: Create `frontend/src/routes/explore/+page.ts`**

```typescript
import { PUBLIC_API_URL } from '$env/static/public';
import type { PageLoad } from './$types';
import type { CorpusStats } from '$lib/corpus-stats';

export const load: PageLoad = async ({ fetch }) => {
    const statsPromise = fetch(`${PUBLIC_API_URL}/corpus/stats`).then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json() as Promise<CorpusStats>;
    });
    return { statsPromise };
};
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd frontend && npx vitest run src/routes/explore/explore.test.ts 2>&1 | tail -10
```

Expected: both tests PASSED

- [ ] **Step 5: Commit**

```bash
git add frontend/src/routes/explore/+page.ts frontend/src/routes/explore/explore.test.ts
git commit -m "feat(corpus): add /explore load function with tests"
```

---

## Task 5: Frontend — `/explore` dashboard page

**Files:**
- Create: `frontend/src/routes/explore/+page.svelte`

- [ ] **Step 1: Create `frontend/src/routes/explore/+page.svelte`**

```svelte
<script lang="ts">
    import type { PageData } from './$types';
    import { toRelativeTime, toBarWidth, toSortedEntries, sortedSourceEntries } from '$lib/corpus-stats';

    let { data }: { data: PageData } = $props();

    let expandedSources = $state<Set<string>>(new Set());

    function toggleSource(source: string) {
        const next = new Set(expandedSources);
        if (next.has(source)) next.delete(source);
        else next.add(source);
        expandedSources = next;
    }
</script>

<svelte:head>
    <title>Explore — Klippy</title>
</svelte:head>

<main class="explore-main">
    <div class="container explore-container">
        <h1 class="page-title">Corpus Explorer</h1>

        {#await data.statsPromise}
            <div class="dashboard">
                <section class="section">
                    <h2 class="section-title">Overview</h2>
                    <div class="stat-cards">
                        {#each [140, 100, 120, 180] as w}
                            <div class="stat-card skeleton" style="width: {w}px; height: 68px"></div>
                        {/each}
                    </div>
                </section>
                <section class="section">
                    <h2 class="section-title">Top Keywords</h2>
                    <div class="keyword-list">
                        {#each Array(10) as _, i}
                            <div class="skeleton" style="height: 20px; width: {60 + (i * 17) % 140}px; border-radius: 2px; margin-bottom: 8px;"></div>
                        {/each}
                    </div>
                </section>
            </div>
        {:then stats}
            {#if stats.overview.total_nodes === 0}
                <div class="empty-state">
                    <p class="empty-message">No documents are indexed yet.</p>
                    <p class="empty-hint">
                        Keywords are extracted during ingestion. Run with
                        <code>--extract-keywords</code> to populate the corpus explorer.
                    </p>
                </div>
            {:else}
                {@const maxKwCount = stats.keywords.top[0]?.count ?? 1}
                {@const totalNodes = stats.overview.total_nodes}

                <div class="dashboard">
                    <section class="section section-overview">
                        <h2 class="section-title">Overview</h2>
                        <div class="stat-cards">
                            <div class="stat-card">
                                <span class="stat-label">Total Nodes</span>
                                <span class="stat-value">{totalNodes.toLocaleString()}</span>
                            </div>
                            <div class="stat-card">
                                <span class="stat-label">Sources</span>
                                <span class="stat-value">{stats.overview.sources.join(', ')}</span>
                            </div>
                            <div class="stat-card">
                                <span class="stat-label">Last Ingested</span>
                                <span class="stat-value">{toRelativeTime(stats.overview.last_ingested)}</span>
                            </div>
                            <div class="stat-card">
                                <span class="stat-label">Date Range</span>
                                <span class="stat-value">
                                    {stats.overview.date_range.from ?? '—'} → {stats.overview.date_range.to ?? '—'}
                                </span>
                            </div>
                        </div>
                    </section>

                    <section class="section">
                        <h2 class="section-title">Top Keywords</h2>
                        <div class="keyword-list">
                            {#each stats.keywords.top as { keyword, count }}
                                <div class="keyword-row">
                                    <span class="keyword-label">{keyword}</span>
                                    <div class="keyword-bar-wrap">
                                        <div class="keyword-bar" style="width: {toBarWidth(count, maxKwCount)}"></div>
                                    </div>
                                    <span class="keyword-count">{count}</span>
                                </div>
                            {/each}
                        </div>
                    </section>

                    <section class="section">
                        <h2 class="section-title">By Source</h2>
                        <div class="breakdown-list">
                            {#each sortedSourceEntries(stats.by_source) as [source, sourceData]}
                                {@const isExpanded = expandedSources.has(source)}
                                <div class="breakdown-row">
                                    <div class="breakdown-header">
                                        <span class="breakdown-label">{source}</span>
                                        <div class="breakdown-bar-wrap">
                                            <div class="breakdown-bar" style="width: {toBarWidth(sourceData.nodes, totalNodes)}"></div>
                                        </div>
                                        <span class="breakdown-count">{sourceData.nodes.toLocaleString()}</span>
                                        <span class="breakdown-pct">{Math.round((sourceData.nodes / totalNodes) * 100)}%</span>
                                        <button
                                            class="expand-btn"
                                            class:expanded={isExpanded}
                                            onclick={() => toggleSource(source)}
                                            aria-label={isExpanded ? `Collapse ${source} keywords` : `Expand ${source} keywords`}
                                        >{isExpanded ? '−' : '+'}</button>
                                    </div>
                                    {#if isExpanded && sourceData.top_keywords.length > 0}
                                        <div class="breakdown-keywords">
                                            {#each sourceData.top_keywords as kw}
                                                <span class="kw-chip">{kw}</span>
                                            {/each}
                                        </div>
                                    {/if}
                                </div>
                            {/each}
                        </div>
                    </section>

                    <section class="section">
                        <h2 class="section-title">By Type</h2>
                        <div class="breakdown-list">
                            {#each toSortedEntries(stats.by_type) as [type, nodeCount]}
                                <div class="breakdown-row">
                                    <div class="breakdown-header">
                                        <span class="breakdown-label">{type}</span>
                                        <div class="breakdown-bar-wrap">
                                            <div class="breakdown-bar" style="width: {toBarWidth(nodeCount, totalNodes)}"></div>
                                        </div>
                                        <span class="breakdown-count">{nodeCount.toLocaleString()}</span>
                                        <span class="breakdown-pct">{Math.round((nodeCount / totalNodes) * 100)}%</span>
                                    </div>
                                </div>
                            {/each}
                        </div>
                    </section>
                </div>
            {/if}
        {:catch}
            <div class="error-banner">
                Failed to load corpus statistics. The backend may be unavailable.
            </div>
        {/await}
    </div>
</main>

<style>
    .explore-main {
        flex: 1;
        overflow-y: auto;
        background: var(--canvas);
    }

    .explore-container {
        max-width: 900px;
        padding-top: var(--size-8);
        padding-bottom: var(--size-10);
    }

    .page-title {
        font-family: var(--font-display);
        font-size: clamp(1.6rem, 3vw, 2.2rem);
        font-weight: 500;
        color: var(--ink-0);
        letter-spacing: -0.01em;
        margin-bottom: var(--size-8);
    }

    .dashboard {
        display: flex;
        flex-direction: column;
        gap: var(--size-8);
    }

    /* ── Section ──────────────────────────────── */
    .section {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 4px;
        padding: var(--size-6);
    }

    .section-title {
        font-family: var(--font-mono);
        font-size: 0.65rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: var(--ink-3);
        font-weight: 500;
        margin-bottom: var(--size-4);
    }

    /* ── Overview stat cards ──────────────────── */
    .stat-cards {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: var(--size-4);
    }

    .stat-card {
        display: flex;
        flex-direction: column;
        gap: var(--size-1);
        padding: var(--size-4);
        background: var(--canvas);
        border: 1px solid var(--border);
        border-radius: 4px;
    }

    .stat-label {
        font-family: var(--font-mono);
        font-size: 0.6rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--ink-3);
        font-weight: 500;
    }

    .stat-value {
        font-family: var(--font-sans);
        font-size: 1rem;
        font-weight: 500;
        color: var(--ink-0);
        line-height: 1.3;
    }

    /* ── Keyword bars ─────────────────────────── */
    .keyword-list {
        display: flex;
        flex-direction: column;
        gap: var(--size-2);
    }

    .keyword-row {
        display: grid;
        grid-template-columns: 180px 1fr 40px;
        align-items: center;
        gap: var(--size-3);
    }

    .keyword-label {
        font-family: var(--font-sans);
        font-size: 0.82rem;
        color: var(--ink-1);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .keyword-bar-wrap {
        height: 6px;
        background: var(--border);
        border-radius: 3px;
        overflow: hidden;
    }

    .keyword-bar {
        height: 100%;
        background: var(--kings-red);
        border-radius: 3px;
        transition: width 0.3s ease;
    }

    .keyword-count {
        font-family: var(--font-mono);
        font-size: 0.72rem;
        color: var(--ink-3);
        text-align: right;
    }

    /* ── Breakdown rows ───────────────────────── */
    .breakdown-list {
        display: flex;
        flex-direction: column;
        gap: var(--size-3);
    }

    .breakdown-row {
        display: flex;
        flex-direction: column;
        gap: var(--size-2);
    }

    .breakdown-header {
        display: grid;
        grid-template-columns: 120px 1fr 60px 44px 28px;
        align-items: center;
        gap: var(--size-3);
    }

    .breakdown-label {
        font-family: var(--font-sans);
        font-size: 0.85rem;
        font-weight: 500;
        color: var(--ink-1);
    }

    .breakdown-bar-wrap {
        height: 8px;
        background: var(--border);
        border-radius: 4px;
        overflow: hidden;
    }

    .breakdown-bar {
        height: 100%;
        background: var(--teal);
        border-radius: 4px;
        transition: width 0.3s ease;
    }

    .breakdown-count {
        font-family: var(--font-mono);
        font-size: 0.72rem;
        color: var(--ink-2);
        text-align: right;
    }

    .breakdown-pct {
        font-family: var(--font-mono);
        font-size: 0.72rem;
        color: var(--ink-3);
        text-align: right;
    }

    .expand-btn {
        background: none;
        border: 1px solid var(--border);
        border-radius: 3px;
        width: 22px;
        height: 22px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        font-size: 0.9rem;
        font-family: var(--font-mono);
        color: var(--ink-2);
        line-height: 1;
        padding: 0;
        transition: color 0.15s, border-color 0.15s;
    }

    .expand-btn:hover,
    .expand-btn.expanded {
        color: var(--kings-red);
        border-color: var(--kings-red);
    }

    .breakdown-keywords {
        display: flex;
        flex-wrap: wrap;
        gap: var(--size-2);
        padding-left: 138px;
    }

    .kw-chip {
        font-family: var(--font-sans);
        font-size: 0.75rem;
        padding: 2px var(--size-2);
        background: var(--canvas);
        border: 1px solid var(--border);
        border-radius: 999px;
        color: var(--ink-2);
    }

    /* ── States ───────────────────────────────── */
    .skeleton {
        background: var(--border);
        border-radius: 2px;
        animation: pulse 1.4s ease-in-out infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 0.4; }
        50%       { opacity: 0.7; }
    }

    .empty-state {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 4px;
        padding: var(--size-10) var(--size-8);
        text-align: center;
    }

    .empty-message {
        font-family: var(--font-display);
        font-size: 1.1rem;
        color: var(--ink-1);
        margin-bottom: var(--size-3);
    }

    .empty-hint {
        font-family: var(--font-sans);
        font-size: 0.85rem;
        color: var(--ink-3);
        line-height: 1.6;
    }

    .empty-hint code {
        font-family: var(--font-mono);
        font-size: 0.8rem;
        background: var(--canvas);
        padding: 2px 6px;
        border-radius: 3px;
        color: var(--kings-red);
    }

    .error-banner {
        background: var(--surface);
        border: 1px solid var(--kings-red);
        border-radius: 4px;
        padding: var(--size-4) var(--size-6);
        font-family: var(--font-sans);
        font-size: 0.9rem;
        color: var(--kings-red);
    }

    /* ── Responsive ───────────────────────────── */
    @media (max-width: 768px) {
        .stat-cards {
            grid-template-columns: repeat(2, 1fr);
        }

        .keyword-row {
            grid-template-columns: 120px 1fr 36px;
        }

        .breakdown-header {
            grid-template-columns: 100px 1fr 50px 36px 24px;
        }

        .breakdown-keywords {
            padding-left: 0;
        }
    }

    @media (max-width: 480px) {
        .stat-cards {
            grid-template-columns: 1fr;
        }
    }
</style>
```

- [ ] **Step 2: Run the full frontend test suite**

```bash
cd frontend && npx vitest run 2>&1 | tail -15
```

Expected: all tests PASSED (no regressions)

- [ ] **Step 3: Commit**

```bash
git add frontend/src/routes/explore/+page.svelte
git commit -m "feat(corpus): add /explore dashboard page"
```

---

## Task 6: Frontend — sidebar Explore nav link

**Files:**
- Modify: `frontend/src/routes/chats/+layout.svelte`

- [ ] **Step 1: Add `Map` to the lucide-svelte import**

In `frontend/src/routes/chats/+layout.svelte`, change:

```typescript
import { Plus, MessageSquare, Pencil, Trash2, ChevronLeft, ChevronRight } from 'lucide-svelte';
```

to:

```typescript
import { Plus, MessageSquare, Pencil, Trash2, ChevronLeft, ChevronRight, Map } from 'lucide-svelte';
```

- [ ] **Step 2: Add the sidebar nav section after `.session-list`**

In `frontend/src/routes/chats/+layout.svelte`, after the closing `</div>` of `.session-list` and before the closing `</aside>`, add:

```svelte
		<nav class="sidebar-nav">
			<a
				href="/explore"
				class="sidebar-nav-link"
				class:active={page.url.pathname.startsWith('/explore')}
				title={isSidebarOpen ? undefined : 'Explore'}
			>
				<Map size={14} />
				{#if isSidebarOpen}
					<span>Explore</span>
				{/if}
			</a>
		</nav>
```

- [ ] **Step 3: Add styles for `.sidebar-nav` and `.sidebar-nav-link`**

In `frontend/src/routes/chats/+layout.svelte` inside `<style>`, append:

```css
	.sidebar-nav {
		border-top: 1px solid var(--border);
		padding: var(--size-2);
	}

	.sidebar-nav-link {
		display: flex;
		align-items: center;
		gap: var(--size-2);
		padding: var(--size-2) var(--size-3);
		border-radius: 4px;
		color: var(--ink-2);
		text-decoration: none;
		font-family: var(--font-sans);
		font-size: 0.85rem;
		transition: background 0.15s, color 0.15s;
	}

	.sidebar-nav-link:hover {
		background: var(--canvas);
		color: var(--ink-0);
	}

	.sidebar-nav-link.active {
		color: var(--kings-red);
	}

	.sidebar.closed .sidebar-nav {
		padding: var(--size-2);
	}

	.sidebar.closed .sidebar-nav-link {
		justify-content: center;
		padding: var(--size-2);
	}
```

- [ ] **Step 4: Run the full frontend test suite**

```bash
cd frontend && npx vitest run 2>&1 | tail -15
```

Expected: all tests PASSED

- [ ] **Step 5: Commit**

```bash
git add frontend/src/routes/chats/+layout.svelte
git commit -m "feat(corpus): add Explore nav link to sidebar"
```

---

## Spec Coverage Check

| Spec requirement | Covered by |
|---|---|
| `GET /corpus/stats` endpoint | Task 2 |
| Qdrant scroll with pagination | Task 2 (Step 3) |
| Comma-separated keyword parsing | Task 1 (Step 4) |
| Top 30 keywords globally, top 5 per source | Task 1 (Steps 4 + tests) |
| `last_ingested` = max date | Task 1 (Step 4) |
| Redis cache key `corpus_stats`, 1h TTL | Task 2 |
| 200 with zeros if empty | Task 2 (test: empty collection) |
| 503 if Qdrant unreachable | Task 2 (test: unreachable) |
| Overview cards (4 stats) | Task 5 |
| Top Keywords with CSS bars | Task 5 |
| By Source with progress bar + toggle | Task 5 |
| By Type with progress bar | Task 5 |
| Loading skeletons | Task 5 (`{#await}` block) |
| Empty corpus state | Task 5 |
| Error banner | Task 5 |
| Sidebar Explore nav link with `Map` icon | Task 6 |
| Relative time display | Task 3 (`toRelativeTime`) |
| Pure CSS bars (no chart library) | Task 5 (inline `width` styles) |
| Responsive layout | Task 5 (media queries) |
