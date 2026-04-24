<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { PUBLIC_API_URL } from '$env/static/public';

	let name = $state('');
	let allNames: string[] = [];
	let filtered = $state<string[]>([]);
	let activeIdx = $state(-1);
	let showDropdown = $state(false);

	onMount(async () => {
		const saved = localStorage.getItem('klippy_user_name');
		if (saved) { goto('/chats/'); return; }

		document.body.style.overflow = '';

		try {
			const [creatorRes, assigneeRes] = await Promise.all([
				fetch(`${PUBLIC_API_URL}/debug/stats?field=creator`),
				fetch(`${PUBLIC_API_URL}/debug/stats?field=assignee`)
			]);
			const names = new Set<string>();
			if (creatorRes.ok) {
				const data = await creatorRes.json();
				for (const n of Object.keys(data.counts ?? {})) names.add(n.trim());
			}
			if (assigneeRes.ok) {
				const data = await assigneeRes.json();
				for (const raw of Object.keys(data.counts ?? {})) {
					for (const n of raw.split(',')) names.add(n.trim());
				}
			}
			allNames = [...names].filter(Boolean).sort();
		} catch { /* backend offline — proceed without suggestions */ }
	});

	function handleInput() {
		const q = name.trim();
		if (!q) { filtered = []; showDropdown = false; return; }
		filtered = allNames.filter((n) => n.toLowerCase().includes(q.toLowerCase()));
		showDropdown = filtered.length > 0;
		activeIdx = -1;
	}

	function select(n: string) {
		name = n;
		showDropdown = false;
	}

	function handleKeydown(e: KeyboardEvent) {
		if (!showDropdown) return;
		if (e.key === 'ArrowDown') {
			e.preventDefault();
			activeIdx = Math.min(activeIdx + 1, filtered.length - 1);
		} else if (e.key === 'ArrowUp') {
			e.preventDefault();
			activeIdx = Math.max(activeIdx - 1, 0);
		} else if (e.key === 'Enter' && activeIdx >= 0) {
			e.preventDefault();
			select(filtered[activeIdx]);
		} else if (e.key === 'Escape') {
			showDropdown = false;
		}
	}

	function handleSubmit(e: Event) {
		e.preventDefault();
		if (!name.trim()) return;
		localStorage.setItem('klippy_user_name', name.trim());
		goto('/chats/');
	}
</script>

<svelte:head>
	<title>Klippy — King's Digital Lab</title>
</svelte:head>

<main class="identity-page">
	<div class="container identity-card">
		<header class="identity-hero">
			<h1 class="heading">Ask anything about<br />your research projects.</h1>
			<p class="hero-description">
				Search across ClickUp tasks, GitHub repositories, and internal documentation.
			</p>
		</header>

		<div class="identity-divider"></div>

		<div class="identity-form-group">
			<p class="form-label">Before we begin, who are you?</p>

		<form onsubmit={handleSubmit} class="identity-form">
			<div class="input-wrap">
				<input
					id="name-input"
					type="text"
					bind:value={name}
					oninput={handleInput}
					onkeydown={handleKeydown}
					onblur={() => setTimeout(() => (showDropdown = false), 150)}
					placeholder="Start typing your name…"
					autocomplete="off"
					spellcheck="false"
				/>

				{#if showDropdown}
					<ul class="dropdown" role="listbox">
						{#each filtered as n, i}
							<li
								role="option"
								aria-selected={i === activeIdx}
								class="dropdown-option"
								class:active={i === activeIdx}
								onmousedown={(e) => { e.preventDefault(); select(n); }}
							>{n}</li>
						{/each}
					</ul>
				{/if}
			</div>

			<button type="submit" class="submit-btn" disabled={!name.trim()}>
				Continue →
			</button>
		</form>
		</div>
	</div>
</main>

<style>
	.identity-page {
		height: calc(100vh - 57px);
		overflow: hidden;
		display: flex;
		align-items: center;
		background: var(--canvas);
	}

	.identity-card {
		width: 100%;
		max-width: 640px;
		padding-bottom: 6vh;
		display: flex;
		flex-direction: column;
		gap: var(--size-8);
	}

	.identity-hero {
		display: flex;
		flex-direction: column;
	}

	.heading {
		font-family: var(--font-display);
		font-size: clamp(2.4rem, 6vw, 3.6rem);
		font-weight: 500;
		line-height: 1.05;
		color: var(--ink-0);
		letter-spacing: -0.01em;
		margin-bottom: var(--size-3);
	}

	.hero-description {
		font-size: 0.95rem;
		line-height: 1.6;
		color: var(--ink-2);
		font-weight: 300;
	}

	.identity-divider {
		height: 1px;
		background: var(--border);
	}

	.identity-form-group {
		display: flex;
		flex-direction: column;
		gap: var(--size-4);
	}

	.form-label {
		font-family: var(--font-mono);
		font-size: 0.7rem;
		text-transform: uppercase;
		letter-spacing: 0.1em;
		color: var(--ink-2);
	}

	.identity-form {
		display: flex;
		flex-direction: column;
		gap: var(--size-3);
	}

	.input-wrap {
		position: relative;
	}

	.input-wrap input {
		width: 100%;
		padding: var(--size-4) var(--size-5);
		background: var(--surface);
		border: 1px solid var(--border);
		border-top: 2px solid var(--kings-red);
		border-radius: 2px;
		font-family: var(--font-sans);
		font-size: 1.1rem;
		font-weight: 400;
		color: var(--ink-0);
		outline: none;
		box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);
	}

	.input-wrap input::placeholder {
		color: var(--ink-3);
	}

	.dropdown {
		position: absolute;
		top: calc(100% + 4px);
		left: 0;
		right: 0;
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: 4px;
		box-shadow: var(--shadow-2);
		list-style: none;
		padding: var(--size-1) 0;
		margin: 0;
		z-index: 100;
		max-height: 220px;
		overflow-y: auto;
	}

	.dropdown-option {
		padding: var(--size-2) var(--size-5);
		font-family: var(--font-sans);
		font-size: 0.95rem;
		color: var(--ink-1);
		cursor: pointer;
		transition: background 0.1s;
	}

	.dropdown-option:hover,
	.dropdown-option.active {
		background: var(--kings-red-light);
		color: var(--kings-red);
	}

	.submit-btn {
		align-self: flex-start;
		padding: var(--size-3) var(--size-6);
		background: var(--kings-red);
		color: #fff;
		border: none;
		border-radius: 2px;
		font-family: var(--font-sans);
		font-size: 0.9rem;
		font-weight: 500;
		cursor: pointer;
		transition: opacity 0.15s;
		letter-spacing: 0.02em;
	}

	.submit-btn:disabled {
		opacity: 0.35;
		cursor: default;
	}

	.submit-btn:not(:disabled):hover {
		opacity: 0.85;
	}
</style>
