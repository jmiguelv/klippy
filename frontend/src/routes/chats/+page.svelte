<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount, tick } from 'svelte';
	import { fade } from 'svelte/transition';
	import { chatState } from '$lib/chat-state.svelte';
	import { PUBLIC_API_URL } from '$env/static/public';
	import { KNOWN_FIELDS } from '$lib/filters';
	import { SlidersHorizontal } from 'lucide-svelte';
	import { slide } from 'svelte/transition';

	interface AcState {
		visible: boolean;
		mode: 'field' | 'value';
		field: string;
		partial: string;
		options: string[];
		activeIdx: number;
	}

	let query = $state('');
	let userName = $state('');
	let questions = $state<string[]>([]);
	let isLoading = $state(true);
	let showSettings = $state(false);
	let topK = $state(10);
	let similarityCutoff = $state(0.3);

	// Autocomplete state
	let ac = $state<AcState>({
		visible: false,
		mode: 'field',
		field: '',
		partial: '',
		options: [],
		activeIdx: 0
	});
	let acCache: Record<string, string[]> = {};

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
		} finally {
			isLoading = false;
		}
	});

	async function fetchValues(field: string): Promise<string[]> {
		if (acCache[field] !== undefined) return acCache[field];
		try {
			const res = await fetch(`${PUBLIC_API_URL}/debug/stats?field=${field}`);
			const data = await res.json();
			acCache[field] = Object.keys(data.counts ?? {});
		} catch {
			acCache[field] = [];
		}
		return acCache[field];
	}

	async function showValueOptions(field: string, partial: string): Promise<void> {
		const values = acCache[field] !== undefined ? acCache[field] : await fetchValues(field);
		const options = values.filter((v) => v.toLowerCase().includes(partial.toLowerCase()));
		ac = { visible: options.length > 0, mode: 'value', field, partial, options, activeIdx: 0 };
	}

	async function handleInput(e: Event) {
		const input = e.target as HTMLInputElement;
		const before = input.value.slice(0, input.selectionStart ?? input.value.length);

		const valueMatch = before.match(/@(\w+):(?:"([^"]*)"|([^"\s]*))$/);
		const fieldMatch = !valueMatch && before.match(/@(\w*)$/);

		if (valueMatch) {
			const [, field, quoted, unquoted] = valueMatch;
			const partial = quoted ?? unquoted;
			if (acCache[field] !== undefined) {
				await showValueOptions(field, partial);
			} else {
				await fetchValues(field);
				const inputEl = e.target as HTMLInputElement;
				const nowBefore = inputEl.value.slice(0, inputEl.selectionStart ?? inputEl.value.length);
				const nowMatch = nowBefore.match(/@(\w+):(?:"([^"]*)"|([^"\s]*))$/);
				if (nowMatch && nowMatch[1] === field) {
					const nowPartial = nowMatch[2] ?? nowMatch[3];
					await showValueOptions(field, nowPartial);
				}
			}
		} else if (fieldMatch) {
			const [, partial] = fieldMatch;
			const options = KNOWN_FIELDS.filter((f) => f.toLowerCase().includes(partial.toLowerCase()));
			ac = {
				visible: options.length > 0,
				mode: 'field',
				field: '',
				partial,
				options,
				activeIdx: 0
			};
		} else {
			ac = { ...ac, visible: false };
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (!ac.visible) return;
		if (e.key === 'ArrowDown') {
			e.preventDefault();
			ac = { ...ac, activeIdx: (ac.activeIdx + 1) % ac.options.length };
		} else if (e.key === 'ArrowUp') {
			e.preventDefault();
			ac = { ...ac, activeIdx: (ac.activeIdx - 1 + ac.options.length) % ac.options.length };
		} else if (e.key === 'Enter' && ac.visible) {
			e.preventDefault();
			selectOption(ac.options[ac.activeIdx]);
		} else if (e.key === 'Escape') {
			ac = { ...ac, visible: false };
		}
	}

	async function selectOption(opt: string) {
		if (ac.mode === 'field') {
			query = query.replace(/@\w*$/, `@${opt}:`);
			ac = { ...ac, visible: false };
			document.getElementById('chats-input')?.focus();
			await showValueOptions(opt, '');
		} else {
			const quotedOpt = opt.includes(' ') ? `"${opt}"` : opt;
			// Hero page doesn't have activeFilters visible but we keep query part
			query = query.replace(new RegExp(`@${ac.field}:(?:"[^"]*"|[^"\\s]*)$`), `@${ac.field}:${quotedOpt} `);
			ac = { ...ac, visible: false };
			document.getElementById('chats-input')?.focus();
		}
	}

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

<section class="composer">
	<div class="container">
		{#if ac.visible}
			<div class="ac-dropdown" role="listbox">
				{#each ac.options as opt, i}
					<button
						type="button"
						role="option"
						aria-selected={i === ac.activeIdx}
						class="ac-option"
						class:ac-active={i === ac.activeIdx}
						onmousedown={(e) => {
							e.preventDefault();
							selectOption(opt);
						}}
					>
						{#if ac.mode === 'field'}
							<span class="ac-prefix">@</span>{opt}<span class="ac-suffix">:</span>
						{:else}
							{opt}
						{/if}
					</button>
				{/each}
			</div>
		{/if}

		<form onsubmit={handleSearch}>
			<div class="composer-input">
				<input
					id="chats-input"
					type="text"
					bind:value={query}
					placeholder="Ask Klippy… use @ to filter by field"
					autocomplete="off"
					oninput={handleInput}
					onkeydown={handleKeydown}
					onblur={() => setTimeout(() => (ac = { ...ac, visible: false }), 300)}
				/>
				<button
					type="button"
					class="settings-toggle"
					class:active={showSettings}
					onclick={async () => {
						showSettings = !showSettings;
						if (showSettings) {
							await tick();
							document.getElementById('slider-topk-hero')?.focus();
						}
					}}
					title="Tune search parameters"
				>
					<SlidersHorizontal size={18} />
				</button>
			</div>

			{#if showSettings}
				<div class="composer-controls" transition:slide>
					<label class="control" for="slider-topk-hero">
						<span class="control-lbl">Top K</span>
						<input id="slider-topk-hero" type="range" min="1" max="50" bind:value={topK} />
						<span class="control-val">{topK}</span>
					</label>
					<label class="control" for="slider-threshold-hero">
						<span class="control-lbl">Threshold</span>
						<input
							id="slider-threshold-hero"
							type="range"
							min="0"
							max="1"
							step="0.05"
							bind:value={similarityCutoff}
						/>
						<span class="control-val">{similarityCutoff.toFixed(2)}</span>
					</label>
				</div>
			{/if}

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
		/* Removed align-items: center to left-align content */
	}

	.hero-section {
		width: 100%;
		/* Match container max-width to align with query box */
		max-width: 1040px;
		padding-top: var(--size-10);
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

	.suggestions-container {
		width: 100%;
		margin-top: var(--size-4);
	}

	.suggestions-label {
		font-family: var(--font-sans);
		font-size: 0.75rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
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

	.question-chip.skeleton {
		background: var(--border);
		border: none;
		cursor: default;
		pointer-events: none;
		animation: pulse 1.5s infinite ease-in-out;
		opacity: 0.5;
	}

	@keyframes pulse {
		0% {
			opacity: 0.3;
		}
		50% {
			opacity: 0.6;
		}
		100% {
			opacity: 0.3;
		}
	}

	/* ── Composer ─────────────────────────────── */
	.composer {
		background: var(--canvas);
		padding: var(--size-6) var(--size-4);
		position: sticky;
		bottom: 0;
		z-index: 100;
		overflow: visible;
	}

	.composer .container {
		position: relative;
		overflow: visible;
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
		display: flex;
		align-items: center;
		gap: var(--size-4);
	}

	.composer-input input {
		flex: 1;
		border: none;
		outline: none;
		background: transparent;
		color: var(--ink-0);
		font-size: 1.1rem;
		font-family: var(--font-sans);
		font-weight: 400;
	}

	.settings-toggle {
		background: none;
		border: none;
		cursor: pointer;
		padding: var(--size-2);
		color: var(--ink-3);
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: 4px;
		transition:
			color 0.15s,
			background 0.15s;
	}

	.settings-toggle:hover,
	.settings-toggle.active {
		color: var(--kings-red);
		background: var(--kings-red-light);
	}

	.composer-controls {
		display: grid;
		grid-template-columns: 1fr 1fr;
		border-top: 1px solid var(--border);
		background: var(--surface);
	}

	.control {
		display: flex;
		align-items: center;
		padding: var(--size-3) var(--size-6);
	}

	.control:first-child {
		border-right: 1px solid var(--border);
	}

	.control-lbl {
		font-family: var(--font-mono);
		font-size: 0.65rem;
		text-transform: uppercase;
		color: var(--ink-2);
		letter-spacing: 0.15em;
		flex: 0 0 90px;
	}

	.control-val {
		font-family: var(--font-mono);
		font-size: 0.75rem;
		color: var(--ink-1);
		flex: 0 0 30px;
		text-align: right;
		font-weight: 500;
	}

	.control input[type='range'] {
		flex: 1;
		appearance: none;
		background: transparent;
		cursor: pointer;
		margin: 0 var(--size-4);
	}

	.control input[type='range']::-webkit-slider-runnable-track {
		background: var(--border);
		height: 2px;
		border-radius: 1px;
	}

	.control input[type='range']::-webkit-slider-thumb {
		appearance: none;
		height: 12px;
		width: 12px;
		background: var(--kings-red);
		border-radius: 50%;
		margin-top: -5px;
		transition: transform 0.1s ease;
	}

	.control input[type='range']::-moz-range-track {
		background: var(--border);
		height: 2px;
		border-radius: 1px;
	}

	.control input[type='range']::-moz-range-thumb {
		border: none;
		height: 12px;
		width: 12px;
		background: var(--kings-red);
		border-radius: 50%;
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

	/* ── Autocomplete dropdown ──────────────────── */
	.ac-dropdown {
		position: absolute;
		bottom: calc(100% + 8px);
		left: 0;
		right: 0;
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: 4px;
		box-shadow: var(--shadow-2);
		overflow: hidden;
		z-index: 1000;
	}

	.ac-option {
		display: block;
		width: 100%;
		text-align: left;
		padding: var(--size-2) var(--size-4);
		background: none;
		border: none;
		cursor: pointer;
		font-family: var(--font-mono);
		font-size: 0.8rem;
		color: var(--ink-1);
		transition: background 0.1s;
		text-shadow: none;
	}

	.ac-option:hover,
	.ac-active {
		background: var(--kings-red-light);
		color: var(--kings-red);
	}

	.ac-prefix,
	.ac-suffix {
		opacity: 0.5;
	}

	@media (max-width: 640px) {
		.hero-section {
			padding: 0 var(--size-4) var(--size-4);
		}

		.composer-input {
			padding: var(--size-3);
		}

		.composer-input input {
			padding: var(--size-2) 0;
		}

		.composer-hint {
			display: none;
		}

		.composer-controls {
			grid-template-columns: 1fr;
		}

		.control {
			padding: var(--size-3) var(--size-4);
		}

		.control-lbl {
			flex: 0 0 70px;
		}

		.control input[type='range'] {
			margin: 0 var(--size-2);
			min-width: 0;
		}

		.control:first-child {
			border-right: none;
			border-bottom: 1px solid var(--border);
		}
	}
</style>
