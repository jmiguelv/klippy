<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { chatState } from '$lib/chat-state.svelte';

	let query = $state('');

	onMount(() => {
		chatState.loadSessions();
		const q = new URLSearchParams(window.location.search).get('q');
		if (q) {
			history.replaceState({}, '', window.location.pathname);
			const id = chatState.createNewChat(q);
			goto(`/chats/${id}/?q=${encodeURIComponent(q)}`);
		}
	});

	function handleSearch(e: Event) {
		e.preventDefault();
		if (!query.trim()) return;
		const id = chatState.createNewChat(query.trim());
		goto(`/chats/${id}/?q=${encodeURIComponent(query.trim())}`);
	}
</script>

<svelte:head>
	<title>Chats — Klippy</title>
</svelte:head>

<main class="chat-main">
	<section class="hero-section container">
		<div class="empty-hero">
			<p class="empty-eyebrow">King's Digital Lab</p>
			<h2 class="empty-heading">What would you like<br />to research today?</h2>

			<div class="quickstart-chips">
				{#each [
					'Summarise my recent tasks',
					"What's in progress this week?",
					'Find open GitHub issues',
					'Show me recent ClickUp updates',
				] as prompt}
					<button
						type="button"
						class="quickstart-chip"
						onclick={() => {
							query = prompt;
							document.getElementById('chats-input')?.focus();
						}}
					>{prompt}</button>
				{/each}
			</div>
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
		justify-content: center;
	}

	.hero-section {
		width: 100%;
		max-width: 800px;
		padding-bottom: 8vh;
	}

	.empty-hero {
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		gap: var(--size-6);
	}

	.empty-eyebrow {
		font-family: var(--font-mono);
		font-size: 0.7rem;
		color: var(--kings-red);
		text-transform: uppercase;
		letter-spacing: 0.12em;
	}

	.empty-heading {
		font-family: var(--font-display);
		font-size: clamp(2rem, 6vw, 3.2rem);
		font-weight: 500;
		line-height: 1.1;
		color: var(--ink-0);
		letter-spacing: -0.01em;
	}

	.quickstart-chips {
		display: flex;
		flex-wrap: wrap;
		gap: var(--size-3);
	}

	.quickstart-chip {
		font-family: var(--font-sans);
		font-size: 0.8rem;
		font-weight: 400;
		color: var(--ink-2);
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: 20px;
		padding: var(--size-2) var(--size-4);
		cursor: pointer;
		transition: border-color 0.15s, color 0.15s;
	}

	.quickstart-chip:hover {
		border-color: var(--kings-red);
		color: var(--ink-0);
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
