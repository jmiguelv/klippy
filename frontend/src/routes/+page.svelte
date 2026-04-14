<script lang="ts">
	import { goto } from '$app/navigation';

	let query = $state('');

	function handleSearch(e: Event) {
		e.preventDefault();
		if (!query.trim()) return;
		goto(`/explore/?q=${encodeURIComponent(query.trim())}`);
	}
</script>

<svelte:head>
	<title>Klippy — Enterprise Search for Research</title>
</svelte:head>

<section class="landing-hero">
	<div class="container hero-inner">
		<header class="hero-text">
			<p class="hero-eyebrow">King's Digital Lab</p>
			<h1 class="hero-heading">Ask anything about your research projects.</h1>
			<p class="hero-description">
				Klippy is an enterprise search aggregator that unifies project management context from
				ClickUp and source code history from GitHub into a single conversational interface.
			</p>
		</header>

		<form class="search-form" onsubmit={handleSearch}>
			<div class="search-input-wrapper">
				<label for="landing-search" class="sr-only">Search projects</label>
				<input
					id="landing-search"
					type="text"
					bind:value={query}
					placeholder="What is project X about?"
					autocomplete="off"
				/>
				<button type="submit" aria-label="Search">
					<svg
						width="20"
						height="20"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						stroke-linecap="round"
						stroke-linejoin="round"
					>
						<circle cx="11" cy="11" r="8"></circle>
						<line x1="21" y1="21" x2="16.65" y2="16.65"></line>
					</svg>
					<span>Explore</span>
				</button>
			</div>
			<p class="search-hint">Search tasks, documentation, and commit history across all spaces.</p>
		</form>
	</div>
</section>

<section class="landing-features">
	<div class="container features-grid">
		<article class="feature-card">
			<h3>Unified Context</h3>
			<p>Bridge the gap between project management and development by indexing tasks and code side-by-side.</p>
		</article>
		<article class="feature-card">
			<h3>Conversational RAG</h3>
			<p>Leverage Retrieval-Augmented Generation to get synthesized answers instead of just a list of links.</p>
		</article>
		<article class="feature-card">
			<h3>Traceable Sources</h3>
			<p>Every answer includes direct citations to the original ClickUp tasks or GitHub repositories.</p>
		</article>
	</div>
</section>

<style>
	.landing-hero {
		padding: var(--size-12) 0 var(--size-10);
		background: linear-gradient(to bottom, var(--surface), var(--canvas));
	}

	.hero-inner {
		max-width: 800px;
		display: flex;
		flex-direction: column;
		gap: var(--size-10);
		text-align: center;
	}

	.hero-eyebrow {
		font-family: var(--font-mono);
		font-size: 0.75rem;
		color: var(--kings-red);
		text-transform: uppercase;
		letter-spacing: 0.15em;
		margin-bottom: var(--size-4);
	}

	.hero-heading {
		font-size: clamp(2.5rem, 8vw, 4rem);
		font-weight: 500;
		line-height: 1.1;
		margin-bottom: var(--size-6);
		color: var(--ink-0);
	}

	.hero-description {
		font-size: 1.1rem;
		line-height: 1.6;
		color: var(--ink-2);
		max-width: 600px;
		margin-inline: auto;
		font-weight: 300;
	}

	.search-form {
		width: 100%;
		max-width: 680px;
		margin-inline: auto;
	}

	.search-input-wrapper {
		display: flex;
		gap: var(--size-3);
		background: var(--surface);
		padding: var(--size-2);
		border: 1px solid var(--border);
		border-top: 3px solid var(--kings-red);
		box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
	}

	input {
		flex: 1;
		border: none;
		padding: var(--size-3) var(--size-4);
		font-size: 1.1rem;
		font-family: var(--font-sans);
		outline: none;
		background: transparent;
	}

	button {
		display: inline-flex;
		align-items: center;
		gap: var(--size-2);
		background: var(--kings-red);
		color: white;
		border: none;
		padding: 0 var(--size-6);
		font-weight: 600;
		cursor: pointer;
		transition: background 0.15s;
	}

	button:hover {
		background: #b00018;
	}

	.search-hint {
		margin-top: var(--size-3);
		font-size: 0.8rem;
		color: var(--ink-2);
		font-family: var(--font-mono);
	}

	.landing-features {
		padding: var(--size-10) 0 var(--size-12);
	}

	.features-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
		gap: var(--size-8);
	}

	.feature-card {
		padding: var(--size-6);
		background: var(--surface);
		border: 1px solid var(--border);
		transition: border-color 0.2s;
	}

	.feature-card:hover {
		border-color: var(--kings-red);
	}

	.feature-card h3 {
		font-family: var(--font-sans);
		font-size: 1.1rem;
		font-weight: 600;
		margin-bottom: var(--size-3);
		color: var(--kings-red);
	}

	.feature-card p {
		font-size: 0.95rem;
		line-height: 1.6;
		color: var(--ink-1);
		font-weight: 300;
	}

	.sr-only {
		position: absolute;
		width: 1px;
		height: 1px;
		padding: 0;
		margin: -1px;
		overflow: hidden;
		clip: rect(0, 0, 0, 0);
		white-space: nowrap;
		border-width: 0;
	}

	@media (max-width: 640px) {
		.search-input-wrapper {
			flex-direction: column;
		}
		button {
			padding: var(--size-3);
			justify-content: center;
		}
	}
</style>
