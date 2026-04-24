<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { chatState } from '$lib/chat-state.svelte';
	import { PUBLIC_API_URL } from '$env/static/public';

	let query = $state('');
	let userName = $state('');
	let questions = $state<string[]>([]);

	onMount(async () => {
		userName = localStorage.getItem('klippy_user_name') ?? '';
		chatState.loadSessions();
		const q = new URLSearchParams(window.location.search).get('q');
		if (q) {
			history.replaceState({}, '', window.location.pathname);
			const id = chatState.createNewChat(q);
			goto(`/chats/${id}/?q=${encodeURIComponent(q)}`); // eslint-disable-line svelte/no-navigation-without-resolve
		}

		try {
			const res = await fetch(`${PUBLIC_API_URL}/questions?n=5`);
			if (res.ok) {
				const data = await res.json();
				questions = data.questions ?? [];
			}
		} catch {
			// backend offline — show nothing
		}
	});

	function handleSearch(e: Event) {
		e.preventDefault();
		if (!query.trim()) return;
		submitQuestion(query.trim());
	}

	function submitQuestion(q: string) {
		const id = chatState.createNewChat(q);
		goto(`/chats/${id}/?q=${encodeURIComponent(q)}`); // eslint-disable-line svelte/no-navigation-without-resolve
	}
</script>

<svelte:head>
	<title>Chats — Klippy</title>
</svelte:head>

<main class="chat-main">
	<section class="hero-section container">
		<div class="empty-hero">
			{#if userName}
				<h2 class="empty-greeting">Hello, {userName}.</h2>
				<p class="empty-subheading">Ask anything about your research projects.</p>
			{:else}
				<h2 class="empty-heading">Ask anything about<br />your research projects.</h2>
			{/if}
			<p class="empty-description">
				Search across ClickUp tasks, GitHub repositories, and internal documentation.
			</p>

			{#if questions.length > 0}
				<div class="question-chips">
					{#each questions as q (q)}
						<button class="question-chip" onclick={() => submitQuestion(q)}>{q}</button>
					{/each}
				</div>
			{/if}
		</div>
	</section>
</main>

<section class="composer">
	<div class="container">
		<form onsubmit={handleSearch}>
			<div class="composer-input">
				<input
					id="chats-input"
					type="text"
					bind:value={query}
					placeholder="Ask Klippy… use @ to filter by field"
					autocomplete="off"
				/>
			</div>
			<p class="composer-hint">
				<kbd>↵</kbd> send · <kbd>@</kbd> filter field
			</p>
		</form>
	</div>
</section>

<style>
	.chat-main {
		flex: 1;
		overflow-y: auto;
		display: flex;
		align-items: center;
	}

	.hero-section {
		width: 100%;
		max-width: 800px;
		padding-bottom: var(--size-8);
	}

	.empty-hero {
		display: flex;
		flex-direction: column;
		align-items: flex-start;
	}

	.empty-greeting {
		font-family: var(--font-display);
		font-size: clamp(1.8rem, 4vw, 2.8rem);
		font-weight: 500;
		line-height: 1.1;
		color: var(--ink-0);
		letter-spacing: -0.01em;
		margin-bottom: var(--size-2);
	}

	.empty-subheading {
		font-family: var(--font-display);
		font-size: 1.1rem;
		font-weight: 300;
		font-style: italic;
		color: var(--ink-1);
		margin-bottom: var(--size-3);
	}

	.empty-heading {
		font-family: var(--font-display);
		font-size: clamp(1.8rem, 4vw, 2.8rem);
		font-weight: 500;
		line-height: 1.1;
		color: var(--ink-0);
		letter-spacing: -0.01em;
		margin-bottom: var(--size-3);
	}

	.empty-description {
		font-size: 0.95rem;
		line-height: 1.6;
		color: var(--ink-2);
		max-width: 480px;
		font-weight: 300;
		margin-bottom: var(--size-6);
	}

	.question-chips {
		display: flex;
		flex-wrap: wrap;
		gap: var(--size-2);
		margin-top: var(--size-4);
	}

	.question-chip {
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: 999px;
		padding: var(--size-2) var(--size-4);
		font-family: var(--font-sans);
		font-size: 0.8rem;
		color: var(--ink-1);
		cursor: pointer;
		transition:
			border-color 0.15s,
			color 0.15s;
		text-align: left;
		line-height: 1.4;
	}

	.question-chip:hover {
		border-color: var(--kings-red);
		color: var(--kings-red);
	}

	/* ── Composer ─────────────────────────────── */
	.composer {
		background: var(--canvas);
		padding: var(--size-6) var(--size-4);
	}

	.composer .container {
		position: relative;
	}

	.composer form {
		background: var(--surface);
		border: 1px solid var(--border);
		border-top: 2px solid var(--kings-red);
		border-radius: 2px;
		padding: 0;
		box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);
		max-width: 1040px;
		margin: 0 auto;
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
</style>
