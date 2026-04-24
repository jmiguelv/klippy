<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	const PLACEHOLDERS = [
		"What's in progress this week?",
		'Summarise my recent ClickUp tasks',
		'Find open GitHub issues for the API',
		'What did the team ship last sprint?',
		'Show docs related to data ingestion',
	];

	let query = $state('');
	let placeholder = $state(PLACEHOLDERS[0]);

	onMount(() => {
		let i = 0;
		const id = setInterval(() => {
			i = (i + 1) % PLACEHOLDERS.length;
			placeholder = PLACEHOLDERS[i];
		}, 3500);
		return () => clearInterval(id);
	});

	function handleSearch(e: Event) {
		e.preventDefault();
		if (!query.trim()) return;
		goto(`/chats?q=${encodeURIComponent(query.trim())}`);
	}
</script>

<svelte:head>
	<title>Klippy — King's Digital Lab</title>
</svelte:head>

<main class="landing-page">
	<section class="landing-hero">
		<div class="container hero-inner">
			<header class="hero-text">
				<p class="hero-eyebrow">King's Digital Lab</p>
				<h1 class="hero-heading">Ask anything about<br />your research projects.</h1>
				<p class="hero-description">
					Search across ClickUp tasks, GitHub repositories,<br class="break" /> and internal documentation.
				</p>
			</header>

			<form class="composer-form" onsubmit={handleSearch}>
				<div class="composer-input">
					<input
						id="landing-search"
						type="text"
						bind:value={query}
						placeholder={placeholder}
						autocomplete="off"
					/>
				</div>
				<p class="composer-hint">
					<kbd>↵</kbd> send · <kbd>@</kbd> filter by field
				</p>
			</form>
		</div>
	</section>
</main>

<style>
	.landing-page {
		flex: 1;
		display: flex;
		flex-direction: column;
	}

	.landing-hero {
		flex: 1;
		display: flex;
		align-items: center;
		padding: var(--size-12) 0;
		background: var(--canvas);
	}

	.hero-inner {
		width: 100%;
		max-width: 800px;
		display: flex;
		flex-direction: column;
		gap: var(--size-12);
		padding-bottom: 10vh;
	}

	.hero-eyebrow {
		font-family: var(--font-mono);
		font-size: 0.7rem;
		color: var(--kings-red);
		text-transform: uppercase;
		letter-spacing: 0.12em;
		margin-bottom: var(--size-6);
	}

	.hero-heading {
		font-size: clamp(3rem, 10vw, 4.8rem);
		font-weight: 500;
		line-height: 1.05;
		margin-bottom: var(--size-6);
		color: var(--ink-0);
		letter-spacing: -0.01em;
	}

	.hero-description {
		font-size: 1rem;
		line-height: 1.6;
		color: var(--ink-2);
		max-width: 520px;
		font-weight: 300;
	}

	.composer-form {
		width: 100%;
		max-width: 640px;
		background: var(--surface);
		border: 1px solid var(--border);
		border-top: 2px solid var(--kings-red);
		border-radius: 2px;
		padding: 0;
		box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);
	}

	.composer-input {
		padding: var(--size-4) var(--size-6);
	}

	.composer-input input {
		width: 100%;
		border: none;
		outline: none;
		background: transparent;
		color: var(--ink-0);
		font-size: 1.1rem;
		font-family: var(--font-sans);
		font-weight: 400;
	}

	.composer-hint {
		padding: var(--size-2) var(--size-6);
		font-family: var(--font-mono);
		font-size: 0.65rem;
		color: var(--ink-3);
		border-top: 1px solid var(--border);
		letter-spacing: 0.02em;
	}

	.composer-hint kbd {
		background: none;
		border: 1px solid var(--border-dark);
		border-radius: 3px;
		padding: 0 4px;
		color: var(--ink-2);
		font-family: var(--font-sans);
		font-size: 0.7rem;
		margin-right: 4px;
		font-weight: 500;
	}

	@media (max-width: 640px) {
		.hero-inner {
			padding-bottom: 0;
		}
		.break {
			display: none;
		}
	}
</style>
