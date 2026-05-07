<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { fade } from 'svelte/transition';
	import { chatState } from '$lib/chat-state.svelte';
	import { PUBLIC_API_URL } from '$env/static/public';
	import Composer from '$lib/Composer.svelte';

	let questions = $state<string[]>([]);
	let isLoading = $state(true);
	let activeFilters = $state<Record<string, string>>({});

	onMount(async () => {
		try {
			const res = await fetch(`${PUBLIC_API_URL}/questions?n=5`);
			if (res.ok) {
				const data = await res.json();
				questions = data.questions ?? [];
			}
		} catch {
			// backend offline — show nothing
		} finally {
			isLoading = false;
		}
	});

	function submitQuestion(text: string) {
		const id = chatState.createNewChat(text, activeFilters);
		goto(`/chats/${id}/?q=${encodeURIComponent(text)}`); 
	}
</script>

<main class="chat-main">
	<section class="hero-section container">
		<div class="empty-hero">
			{#if chatState.userName}
				<h2 class="empty-greeting">Hello, {chatState.userName}.</h2>
				<p class="empty-subheading">Ask anything about your research projects.</p>
			{:else}
				<h2 class="empty-heading">Ask anything about<br />your research projects.</h2>
			{/if}
			<p class="empty-description">
				Search across ClickUp tasks, GitHub repositories, and internal documentation.
			</p>

			{#if isLoading || questions.length > 0}
				<div class="suggestions-container" in:fade={{ duration: 200 }}>
					<p class="suggestions-label">Sample queries based on indexed docs:</p>
					<div class="question-chips">
						{#if isLoading}
							<div class="question-chip skeleton" style="width: 150px; height: 32px"></div>
							<div class="question-chip skeleton" style="width: 220px; height: 32px"></div>
							<div class="question-chip skeleton" style="width: 180px; height: 32px"></div>
							<div class="question-chip skeleton" style="width: 250px; height: 32px"></div>
						{:else}
							{#each questions as q (q)}
								<button class="question-chip" onclick={() => submitQuestion(q)}>{q}</button>
							{/each}
						{/if}
					</div>
				</div>
			{/if}
		</div>
	</section>
</main>

<section class="composer-section">
	<div class="container">
		<Composer
			onSend={submitQuestion}
			bind:activeFilters
		/>
	</div>
</section>

<style>
	.chat-main {
		flex: 1;
		overflow-y: auto;
		display: flex;
	}

	.hero-section {
		width: 100%;
		max-width: 1040px;
		padding-top: var(--size-8);
		padding-bottom: var(--size-8);
	}

	.empty-hero {
		display: flex;
		flex-direction: column;
		align-items: flex-start;
	}

	.empty-greeting,
	.empty-heading {
		font-family: var(--font-display);
		font-size: var(--text-hero);
		font-weight: 500;
		line-height: 1.1;
		color: var(--ink-0);
		letter-spacing: -0.01em;
		margin-bottom: var(--size-3);
	}

	.empty-greeting {
		margin-bottom: var(--size-2);
	}

	.empty-subheading {
		font-family: var(--font-display);
		font-size: var(--text-xl);
		font-weight: 300;
		font-style: italic;
		color: var(--ink-1);
		margin-bottom: var(--size-3);
	}

	.empty-description {
		font-size: var(--text-md);
		line-height: 1.6;
		color: var(--ink-2);
		max-width: 480px;
		font-weight: 300;
		margin-bottom: var(--size-6);
	}

	.suggestions-container {
		width: 100%;
		margin-top: var(--size-4);
	}

	.suggestions-label {
		font-family: var(--font-mono);
		font-size: var(--text-sm);
		text-transform: uppercase;
		letter-spacing: 0.12em;
		color: var(--ink-3);
		margin-bottom: var(--size-2);
		font-weight: 600;
	}

	.question-chips {
		display: flex;
		flex-wrap: wrap;
		gap: var(--size-2);
	}

	.question-chip {
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius-pill);
		padding: var(--size-2) var(--size-4);
		font-family: var(--font-sans);
		font-size: var(--text-base-sm);
		color: var(--ink-1);
		cursor: pointer;
		transition:
			border-color var(--ease-base),
			color var(--ease-base);
		text-align: left;
		line-height: 1.4;
	}

	.question-chip:hover {
		border-color: var(--kings-red);
		color: var(--kings-red);
	}

	.question-chip.skeleton {
		border: none;
		cursor: default;
		pointer-events: none;
	}

	@media (max-width: 640px) {
		.hero-section {
			padding: 0 var(--size-4) var(--size-4);
		}
	}
</style>
