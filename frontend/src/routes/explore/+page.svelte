<script lang="ts">
	import type { PageData } from './$types';
	import { toRelativeTime, toBarWidth, toSortedEntries, sortedSourceEntries } from '$lib/corpus-stats';

	let { data }: { data: PageData } = $props();
</script>

<svelte:head>
	<title>Explore — Klippy</title>
</svelte:head>

<main class="explore-main">
	<div class="container explore-container">
		<h1 class="page-title">Corpus Explorer</h1>

		{#await data.statsPromise}
			<div class="dashboard" aria-busy="true">
				<section class="card">
					<h2 class="section-label">Overview</h2>
					<dl class="stat-grid">
						{#each [140, 100, 120, 180] as w}
							<div class="stat">
								<dt class="skeleton" style="width:60px;height:10px"></dt>
								<dd class="skeleton" style="width:{w}px;height:22px;margin-top:4px"></dd>
							</div>
						{/each}
					</dl>
				</section>
				<section class="card">
					<h2 class="section-label">Top Keywords</h2>
					<ul class="keyword-list" aria-label="Loading keywords">
						{#each Array(8) as _, i}
							<li class="keyword-row">
								<span class="skeleton" style="width:{60 + (i * 17) % 140}px;height:14px"></span>
							</li>
						{/each}
					</ul>
				</section>
			</div>
		{:then stats}
			{#if stats.overview.total_nodes === 0}
				<p class="empty-state">
					No documents are indexed yet.<br />
					Run ingestion with <code>--extract-keywords</code> to populate the corpus explorer.
				</p>
			{:else}
				{@const max = stats.keywords.top[0]?.count ?? 1}
				{@const total = stats.overview.total_nodes}

				<div class="dashboard">
					<section class="card">
						<h2 class="section-label">Overview</h2>
						<dl class="stat-grid">
							<div class="stat">
								<dt>Total Nodes</dt>
								<dd>{total.toLocaleString()}</dd>
							</div>
							<div class="stat">
								<dt>Sources</dt>
								<dd>{stats.overview.sources.join(', ')}</dd>
							</div>
							<div class="stat">
								<dt>Last Ingested</dt>
								<dd>{toRelativeTime(stats.overview.last_ingested)}</dd>
							</div>
							<div class="stat">
								<dt>Date Range</dt>
								<dd>{stats.overview.date_range.from ?? '—'} → {stats.overview.date_range.to ?? '—'}</dd>
							</div>
						</dl>
					</section>

					<section class="card">
						<h2 class="section-label">Top Keywords</h2>
						<ul class="keyword-list">
							{#each stats.keywords.top as { keyword, count }}
								<li class="keyword-row">
									<span class="kw-label">{keyword}</span>
									<span class="bar-track" role="presentation">
										<span class="bar bar-red" style="width:{toBarWidth(count, max)}"></span>
									</span>
									<span class="kw-count">{count}</span>
								</li>
							{/each}
						</ul>
					</section>

					<section class="card">
						<h2 class="section-label">By Source</h2>
						<ul class="breakdown-list">
							{#each sortedSourceEntries(stats.by_source) as [source, src]}
								<li>
									<details>
										<summary class="breakdown-row">
											<span class="bd-label">{source}</span>
											<span class="bar-track" role="presentation">
												<span class="bar bar-navy" style="width:{toBarWidth(src.nodes, total)}"></span>
											</span>
											<span class="bd-count">{src.nodes.toLocaleString()}</span>
											<span class="bd-pct">{Math.round((src.nodes / total) * 100)}%</span>
										</summary>
										{#if src.top_keywords.length > 0}
											<ul class="kw-chips">
												{#each src.top_keywords as kw}
													<li class="kw-chip">{kw}</li>
												{/each}
											</ul>
										{/if}
									</details>
								</li>
							{/each}
						</ul>
					</section>

					<section class="card">
						<h2 class="section-label">By Type</h2>
						<ul class="breakdown-list">
							{#each toSortedEntries(stats.by_type) as [type, count]}
								<li class="breakdown-row no-toggle">
									<span class="bd-label">{type}</span>
									<span class="bar-track" role="presentation">
										<span class="bar bar-navy" style="width:{toBarWidth(count, total)}"></span>
									</span>
									<span class="bd-count">{count.toLocaleString()}</span>
									<span class="bd-pct">{Math.round((count / total) * 100)}%</span>
								</li>
							{/each}
						</ul>
					</section>
				</div>
			{/if}
		{:catch}
			<p class="error-banner" role="alert">
				Failed to load corpus statistics. The backend may be unavailable.
			</p>
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
		gap: var(--size-6);
	}

	/* ── Card ─────────────────────────────────── */
	.card {
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: 4px;
		padding: var(--size-5) var(--size-6);
	}

	.section-label {
		font-family: var(--font-mono);
		font-size: 0.65rem;
		text-transform: uppercase;
		letter-spacing: 0.12em;
		color: var(--ink-3);
		font-weight: 500;
		margin-bottom: var(--size-4);
	}

	/* ── Overview dl ──────────────────────────── */
	.stat-grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: var(--size-4);
	}

	.stat {
		padding: var(--size-3) var(--size-4);
		background: var(--canvas);
		border: 1px solid var(--border);
		border-radius: 4px;
	}

	.stat dt {
		font-family: var(--font-mono);
		font-size: 0.6rem;
		text-transform: uppercase;
		letter-spacing: 0.1em;
		color: var(--ink-3);
	}

	.stat dd {
		font-family: var(--font-sans);
		font-size: 1rem;
		font-weight: 500;
		color: var(--ink-0);
		margin-top: var(--size-1);
		line-height: 1.3;
	}

	/* ── Keyword list ─────────────────────────── */
	.keyword-list {
		list-style: none;
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

	.kw-label {
		font-family: var(--font-sans);
		font-size: 0.82rem;
		color: var(--ink-1);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.kw-count {
		font-family: var(--font-mono);
		font-size: 0.72rem;
		color: var(--ink-3);
		text-align: right;
	}

	/* ── Breakdown list ───────────────────────── */
	.breakdown-list {
		list-style: none;
		display: flex;
		flex-direction: column;
		gap: var(--size-2);
	}

	.breakdown-row,
	details > summary.breakdown-row {
		display: grid;
		grid-template-columns: 120px 1fr 60px 44px;
		align-items: center;
		gap: var(--size-3);
		list-style: none;
		cursor: pointer;
		padding: var(--size-1) 0;
	}

	details > summary { list-style: none; }
	details > summary::-webkit-details-marker { display: none; }

	.breakdown-row.no-toggle { cursor: default; }

	.bd-label {
		font-family: var(--font-sans);
		font-size: 0.85rem;
		font-weight: 500;
		color: var(--ink-1);
	}

	.bd-count {
		font-family: var(--font-mono);
		font-size: 0.72rem;
		color: var(--ink-2);
		text-align: right;
	}

	.bd-pct {
		font-family: var(--font-mono);
		font-size: 0.72rem;
		color: var(--ink-3);
		text-align: right;
	}

	/* ── Shared bar ───────────────────────────── */
	.bar-track {
		height: 7px;
		background: var(--border);
		border-radius: 3px;
		overflow: hidden;
		display: block;
	}

	.bar {
		display: block;
		height: 100%;
		border-radius: 3px;
		transition: width 0.3s ease;
	}

	.bar-red  { background: var(--kings-red); }
	.bar-navy { background: #0a2d50; }

	/* ── Source keyword chips ─────────────────── */
	.kw-chips {
		list-style: none;
		display: flex;
		flex-wrap: wrap;
		gap: var(--size-2);
		padding: var(--size-2) 0 var(--size-1) 138px;
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
		display: block;
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
		font-family: var(--font-sans);
		font-size: 0.9rem;
		color: var(--ink-2);
		line-height: 1.8;
	}

	.empty-state code {
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
		.stat-grid { grid-template-columns: repeat(2, 1fr); }
		.keyword-row { grid-template-columns: 120px 1fr 36px; }
		.breakdown-row,
		details > summary.breakdown-row {
			grid-template-columns: 100px 1fr 50px 36px;
		}
		.kw-chips { padding-left: 0; }
	}

	@media (max-width: 480px) {
		.stat-grid { grid-template-columns: 1fr; }
	}
</style>
