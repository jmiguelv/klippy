<script lang="ts">
	import { tick } from 'svelte';
	import { slide } from 'svelte/transition';
	import { SlidersHorizontal } from 'lucide-svelte';
	import { chatState } from '$lib/chat-state.svelte';
	import { createAutocomplete } from '$lib/use-autocomplete';
	import { page } from '$app/state';

	interface Props {
		onSend: (text: string) => void;
		placeholder?: string;
		showSettings?: boolean;
		activeFilters?: Record<string, string>;
	}

	let {
		onSend,
		placeholder = 'Ask Klippy… use @ to filter by field',
		showSettings: canShowSettings = true,
		activeFilters = $bindable({})
	}: Props = $props();

	let query = $state('');
	let showSettings = $state(false);
	let modelName = $state('...');
	const ac = createAutocomplete();

	$effect(() => {
		if (typeof window !== 'undefined') {
			modelName = localStorage.getItem('klippy_model_name') || '...';
		}
	});

	function parseFilters(raw: string): { text: string; filters: Record<string, string> } {
		const filters: Record<string, string> = {};
		const text = raw
			.replace(/@(\w+):(?:"([^"]+)"|(\S+))/g, (_, k, quoted, unquoted) => {
				filters[k] = quoted ?? unquoted;
				return '';
			})
			.trim();
		return { text, filters };
	}

	async function handleSend(e?: Event) {
		e?.preventDefault();
		const raw = query.trim();
		if (!raw) return;

		const { text, filters: parsed } = parseFilters(raw);
		activeFilters = { ...activeFilters, ...parsed };
		query = '';
		ac.close();
		onSend(text);
	}

	function removeFilter(key: string) {
		const { [key]: _, ...rest } = activeFilters;
		activeFilters = rest;
	}

	async function selectOption(opt: string) {
		if (ac.state.mode === 'field') {
			query = query.replace(/@\w*$/, `@${opt}:`);
			ac.close();
			document.getElementById('composer-input-el')?.focus();
			// Re-trigger value autocomplete
			const input = document.getElementById('composer-input-el') as HTMLInputElement;
			if (input) {
				await ac.handleInput(query, query.length);
			}
		} else {
			activeFilters = { ...activeFilters, [ac.state.field]: opt };
			query = query.replace(new RegExp(`@${ac.state.field}:(?:"[^"]*"|[^"\\s]*)$`), '').trimEnd();
			ac.close();
			document.getElementById('composer-input-el')?.focus();
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (ac.state.visible) {
			ac.handleKeydown(e, selectOption);
		}
	}

	let hasFilters = $derived(Object.keys(activeFilters).length > 0);
	let sessionId = $derived(page.params.id ? page.params.id.split('-')[0].toUpperCase() : '');
</script>

<div class="composer-container">
	{#if ac.state.visible}
		<div class="ac-dropdown" role="listbox">
			{#each ac.state.options as opt, i}
				<button
					type="button"
					role="option"
					aria-selected={i === ac.state.activeIdx}
					class="ac-option"
					class:ac-active={i === ac.state.activeIdx}
					onmousedown={(e) => {
						e.preventDefault();
						selectOption(opt);
					}}
				>
					{#if ac.state.mode === 'field'}
						<span class="ac-prefix">@</span>{opt}<span class="ac-suffix">:</span>
					{:else}
						{opt}
					{/if}
				</button>
			{/each}
		</div>
	{/if}

	<form onsubmit={handleSend}>
		<div class="composer-input">
			{#if hasFilters}
				<div class="filter-chips">
					{#each Object.entries(activeFilters) as [key, value]}
						<span class="chip">
							<span class="chip-label">
								<span class="chip-key">{key}</span><span class="chip-sep">:</span><span
									class="chip-val">{value}</span
								>
							</span>
							<button
								type="button"
								class="chip-remove"
								onclick={() => removeFilter(key)}
								aria-label="Remove {key} filter">×</button
							>
						</span>
					{/each}
				</div>
			{/if}
			<input
				id="composer-input-el"
				type="text"
				bind:value={query}
				{placeholder}
				autocomplete="off"
				oninput={(e) =>
					ac.handleInput(
						(e.target as HTMLInputElement).value,
						(e.target as HTMLInputElement).selectionStart || 0
					)}
				onkeydown={handleKeydown}
				onblur={() => setTimeout(() => ac.close(), 300)}
			/>
			{#if canShowSettings}
				<button
					type="button"
					class="settings-toggle"
					class:active={showSettings}
					onclick={async () => {
						showSettings = !showSettings;
						if (showSettings) {
							await tick();
							document.getElementById('slider-topk')?.focus();
						}
					}}
					title="Tune search parameters"
				>
					<SlidersHorizontal size={18} />
				</button>
			{/if}
		</div>

		{#if showSettings}
			<div class="composer-controls" transition:slide>
				<label class="control" for="slider-topk">
					<span class="control-lbl">Top K</span>
					<input id="slider-topk" type="range" min="1" max="50" bind:value={chatState.topK} />
					<span class="control-val">{chatState.topK}</span>
				</label>
				<label class="control" for="slider-threshold">
					<span class="control-lbl">Threshold</span>
					<input
						id="slider-threshold"
						type="range"
						min="0"
						max="1"
						step="0.05"
						bind:value={chatState.threshold}
					/>
					<span class="control-val">{chatState.threshold.toFixed(2)}</span>
				</label>
			</div>
		{/if}

		<p class="composer-hint">
			<span class="hint-items">
				<kbd>↵</kbd> send · <kbd>@</kbd> filter field
			</span>
			{#if sessionId || modelName}
				<span class="composer-meta">
					{#if sessionId}session <b>{sessionId}</b>{/if}
					{#if sessionId && modelName} · {/if}
					{#if modelName}{modelName}{/if}
				</span>
			{/if}
		</p>
	</form>
</div>

<style>
	.composer-container {
		position: relative;
		overflow: visible;
	}

	form {
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
		flex-wrap: wrap;
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
		min-width: 200px;
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

	.filter-chips {
		display: flex;
		flex-wrap: nowrap;
		gap: var(--size-2);
		padding-bottom: var(--size-3);
		overflow-x: auto;
		max-width: 100%;
		scrollbar-width: none;
	}

	.filter-chips::-webkit-scrollbar {
		display: none;
	}

	.chip {
		display: inline-flex;
		align-items: center;
		gap: var(--size-2);
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: 4px;
		padding: 2px 4px 2px 8px;
		font-size: 0.72rem;
		font-family: var(--font-mono);
		line-height: 1.4;
	}

	.chip-key {
		color: var(--kings-red);
		font-weight: 600;
	}

	.chip-sep {
		color: var(--ink-3);
	}

	.chip-val {
		color: var(--ink-1);
	}

	.chip-remove {
		background: none;
		border: none;
		cursor: pointer;
		color: var(--ink-3);
		padding: 0 2px;
		font-size: 0.9rem;
		line-height: 1;
		display: flex;
		align-items: center;
	}

	.chip-remove:hover {
		color: var(--ink-0);
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
		display: flex;
		justify-content: space-between;
		align-items: center;
		border-top: 1px solid var(--border);
		letter-spacing: 0.02em;
	}

	.hint-items {
		display: flex;
		align-items: center;
		gap: 2px;
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

	.composer-meta {
		text-transform: uppercase;
		letter-spacing: 0.08em;
		opacity: 0.8;
		font-weight: 500;
	}

	.composer-meta b {
		color: var(--ink-1);
	}

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
		.composer-input {
			padding: var(--size-3);
		}

		.composer-input input {
			padding: var(--size-2) 0;
		}

		.filter-chips {
			flex-wrap: wrap;
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
