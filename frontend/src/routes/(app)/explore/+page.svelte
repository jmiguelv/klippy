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
        min-height: 0;
        overflow-y: auto;
        background: var(--canvas);
    }

    .explore-container {
        max-width: 1040px;
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
        background: #0a2d50;
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
