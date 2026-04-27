<script lang="ts">
	import { onMount, tick, untrack } from 'svelte';
	import { slide } from 'svelte/transition';
	import { PUBLIC_API_URL } from '$env/static/public';
	import { KNOWN_FIELDS } from '$lib/filters';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { chatState } from '$lib/chat-state.svelte';
	import { marked } from 'marked';
	import {
		Trash2,
		ChevronDown,
		ThumbsUp,
		ThumbsDown,
		RotateCcw,
		Search,
		Code,
		FileText,
		SlidersHorizontal
	} from 'lucide-svelte';

	interface AcState {
		visible: boolean;
		mode: 'field' | 'value';
		field: string;
		partial: string;
		options: string[];
		activeIdx: number;
	}

	// Per-session UI state — reset when params.id changes
	let expandedSources = $state<Set<number>>(new Set());
	let activeFilters = $state<Record<string, string>>({});
	let query = $state('');
	let isLoading = $state(false);
	let topK = $state(10);
	let similarityCutoff = $state(0.3);
	let modelName = $state('...');
	let showSettings = $state(false);
	let chatMainEl: HTMLElement;

	// Reset per-session state when navigating between sessions
	$effect(() => {
		const id = page.params.id;
		const session = untrack(() => chatState.sessions.find((s) => s.id === id));
		activeFilters = session?.filters ? { ...session.filters } : {};
		expandedSources = new Set();
	});

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
	let allStatsReady: Promise<void> | null = null;
	let statsOffline = $state(false);

	function toggleSources(index: number) {
		if (expandedSources.has(index)) {
			expandedSources.delete(index);
		} else {
			expandedSources.add(index);
		}
		expandedSources = new Set(expandedSources);
	}

	function deleteExchange(i: number) {
		const sIdx = chatState.sessions.findIndex((s) => s.id === page.params.id);
		if (sIdx === -1) return;
		chatState.sessions[sIdx].messages = chatState.sessions[sIdx].messages.filter(
			(_, idx) => idx !== i && idx !== i + 1
		);
		chatState.saveSessions();
	}

	function truncate(str: string, n: number) {
		return str.length > n ? str.slice(0, n - 1) + '...' : str;
	}

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

	function removeFilter(key: string) {
		const { [key]: _, ...rest } = activeFilters;
		activeFilters = rest;
		const sIdx = chatState.sessions.findIndex((s) => s.id === page.params.id);
		if (sIdx !== -1) {
			chatState.sessions[sIdx].filters = activeFilters;
			chatState.saveSessions();
		}
	}

	// ── Autocomplete ────────────────────────────────────────────

	const AC_CACHE_TTL_MS = 3_600_000;
	const AC_CACHE_LS_KEY = 'klippy_ac_cache';

	async function fetchAllStats(): Promise<void> {
		try {
			const stored = localStorage.getItem(AC_CACHE_LS_KEY);
			if (stored) {
				const { timestamp, stats } = JSON.parse(stored) as {
					timestamp: number;
					stats: Record<string, string[]>;
				};
				if (Date.now() - timestamp < AC_CACHE_TTL_MS) {
					Object.assign(acCache, stats);
					return;
				}
			}
		} catch {
			/* ignore */
		}

		try {
			const res = await fetch(`${PUBLIC_API_URL}/debug/stats/all`);
			const data = (await res.json()) as Record<string, Record<string, number>>;
			const stats: Record<string, string[]> = {};
			for (const [field, valueCounts] of Object.entries(data)) {
				stats[field] = Object.keys(valueCounts);
			}
			Object.assign(acCache, stats);
			localStorage.setItem(AC_CACHE_LS_KEY, JSON.stringify({ timestamp: Date.now(), stats }));
		} catch {
			statsOffline = true;
		}
	}

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
		if (acCache[field] === undefined && allStatsReady) await allStatsReady;
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
			document.getElementById('chat-input')?.focus();
			await showValueOptions(opt, '');
		} else {
			activeFilters = { ...activeFilters, [ac.field]: opt };
			const quotedOpt = opt.includes(' ') ? `"${opt}"` : opt;
			query = query.replace(new RegExp(`@${ac.field}:(?:"[^"]*"|[^"\\s]*)$`), '').trimEnd();
			ac = { ...ac, visible: false };
			document.getElementById('chat-input')?.focus();
		}
	}

	// ── Send ────────────────────────────────────────────────────

	async function sendFeedback(isPositive: boolean, sessionId: string) {
		try {
			await fetch(`${PUBLIC_API_URL}/feedback`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ session_id: sessionId, is_positive: isPositive })
			});
			if (!isPositive) {
				alert('Session history cleared on server. Starting fresh!');
				const sIdx = chatState.sessions.findIndex((s) => s.id === sessionId);
				if (sIdx !== -1) {
					chatState.sessions[sIdx].messages = [];
					chatState.saveSessions();
				}
			}
		} catch (e) {
			console.error(e);
		}
	}

	async function handleSend(textOverride?: string, isRefresh = false) {
		const raw = textOverride || query.trim();
		if (!raw) return;

		const { text, filters: parsed } = parseFilters(raw);
		activeFilters = { ...activeFilters, ...parsed };
		ac = { ...ac, visible: false };

		if (!textOverride) {
			query = '';
		}

		const sessionId = page.params.id;
		const sIdx = chatState.sessions.findIndex((s) => s.id === sessionId);
		if (sIdx === -1) return;

		if (chatState.sessions[sIdx].messages.length === 0) {
			chatState.sessions[sIdx].title = truncate(text, 35);
		}

		chatState.sessions[sIdx].filters = { ...activeFilters };

		if (!isRefresh) {
			chatState.sessions[sIdx].messages = [
				...chatState.sessions[sIdx].messages,
				{
					role: 'user',
					content: text,
					filters: Object.keys(activeFilters).length ? { ...activeFilters } : undefined
				}
			];
			await tick();
			chatMainEl?.scrollTo({ top: chatMainEl.scrollHeight, behavior: 'smooth' });
		}
		chatState.sessions[sIdx].updatedAt = Date.now();

		isLoading = true;

		if (isRefresh) {
			await fetch(`${PUBLIC_API_URL}/feedback`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ session_id: sessionId, is_positive: false })
			});
		}

		const startTime = Date.now();
		const streamingMessage = {
			role: 'klippy' as const,
			content: '',
			steps: [
				{
					label: 'Parsing query',
					detail:
						Object.keys(activeFilters).length > 0
							? `${Object.keys(activeFilters).length} filter${Object.keys(activeFilters).length > 1 ? 's' : ''} active`
							: 'no filters',
					t: Date.now() - startTime,
					active: false
				},
				{
					label: 'Searching Qdrant',
					detail: `top_k=${topK} · threshold=${similarityCutoff.toFixed(2)}`,
					t: null,
					active: true
				}
			]
		};

		if (isRefresh) {
			chatState.sessions[sIdx].messages[chatState.sessions[sIdx].messages.length - 1] =
				streamingMessage;
		} else {
			chatState.sessions[sIdx].messages = [...chatState.sessions[sIdx].messages, streamingMessage];
		}
		const msgIdx = chatState.sessions[sIdx].messages.length - 1;

		await tick();
		chatMainEl?.scrollTo({ top: chatMainEl.scrollHeight, behavior: 'smooth' });

		try {
			const response = await fetch(`${PUBLIC_API_URL}/query-stream`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					text,
					session_id: sessionId,
					filters: activeFilters,
					top_k: topK,
					similarity_cutoff: similarityCutoff > 0 ? similarityCutoff : null
				})
			});

			if (!response.ok || !response.body) throw new Error(`HTTP ${response.status}`);

			const reader = response.body.getReader();
			const decoder = new TextDecoder();
			let buffer = '';

			let pendingText = '';
			let rafId: number | null = null;
			const rafFlush = () => {
				if (pendingText) {
					chatState.sessions[sIdx].messages[msgIdx] = {
						...chatState.sessions[sIdx].messages[msgIdx],
						content: chatState.sessions[sIdx].messages[msgIdx].content + pendingText
					};
					pendingText = '';
					tick().then(() =>
						chatMainEl?.scrollTo({ top: chatMainEl.scrollHeight, behavior: 'smooth' })
					);
				}
				rafId = null;
			};

			while (true) {
				const { done, value } = await reader.read();
				if (done) break;
				buffer += decoder.decode(value, { stream: true });

				const parts = buffer.split('\n\n');
				buffer = parts.pop() ?? '';

				for (const part of parts) {
					if (!part.startsWith('data: ')) continue;
					const evt = JSON.parse(part.slice(6));

					if (evt.type === 'meta') {
						if (evt.model) {
							modelName = evt.model.toUpperCase();
							localStorage.setItem('klippy_model_name', modelName);
						}
					} else if (evt.type === 'retrieved') {
						const searchTime = Date.now() - startTime;
						const steps = chatState.sessions[sIdx].messages[msgIdx].steps || [];
						if (steps[1]) {
							steps[1].active = false;
							steps[1].t = searchTime;
						}
						const numSources = evt.num_sources || 0;
						steps.push({
							label: `Retrieved ${numSources} chunk${numSources === 1 ? '' : 's'}`,
							detail: 'Ranked by semantic relevance',
							t: searchTime,
							active: false
						});
						steps.push({
							label: 'Synthesising',
							detail: 'Reasoning across retrieved chunks',
							t: null,
							active: true
						});
						chatState.sessions[sIdx].messages[msgIdx].steps = steps;
						chatState.sessions[sIdx].messages[msgIdx] = {
							...chatState.sessions[sIdx].messages[msgIdx]
						};
					} else if (evt.type === 'chunk') {
						pendingText += evt.text;
						if (!rafId) rafId = requestAnimationFrame(rafFlush);
					} else if (evt.type === 'done') {
						if (rafId) {
							cancelAnimationFrame(rafId);
							rafId = null;
						}
						rafFlush();
						const totalTime = Date.now() - startTime;
						const steps = chatState.sessions[sIdx].messages[msgIdx].steps || [];
						if (steps[3]) {
							steps[3].active = false;
							steps[3].t = totalTime - (steps[1]?.t || 0);
						}
						chatState.sessions[sIdx].messages[msgIdx] = {
							...chatState.sessions[sIdx].messages[msgIdx],
							steps,
							sources: evt.sources,
							total_time_ms: evt.total_time_ms,
							cached_at: evt.cached_at,
							context_length: evt.context_length
						};
					} else if (evt.type === 'error') {
						chatState.sessions[sIdx].messages[msgIdx] = {
							...chatState.sessions[sIdx].messages[msgIdx],
							content: `Error: ${evt.detail}`
						};
					}
				}
			}

			chatState.sessions[sIdx].updatedAt = Date.now();
			chatState.saveSessions();
		} catch (e) {
			console.error(e);
			chatState.sessions[sIdx].messages[msgIdx] = {
				...chatState.sessions[sIdx].messages[msgIdx],
				content: 'Error: Could not connect to the research engine.'
			};
			chatState.saveSessions();
		} finally {
			isLoading = false;
			await tick();
			chatMainEl?.scrollTo({ top: chatMainEl.scrollHeight, behavior: 'smooth' });
		}
	}

	// Derived
	let currentSession = $derived(chatState.sessions.find((s) => s.id === page.params.id));
	let chatHistory = $derived(currentSession?.messages || []);
	let hasFilters = $derived(Object.keys(activeFilters).length > 0);

	onMount(() => {
		chatState.loadSessions();
		const session = chatState.sessions.find((s) => s.id === page.params.id);
		if (!session) {
			goto('/chats/');
			return;
		}

		allStatsReady = fetchAllStats();

		const savedModel = localStorage.getItem('klippy_model_name');
		if (savedModel) modelName = savedModel;

		const q = new URLSearchParams(window.location.search).get('q');
		if (q) {
			history.replaceState({}, '', window.location.pathname);
			handleSend(q);
		}
	});
</script>

<svelte:head>
	<title>{currentSession?.title ?? 'Chat'} — Klippy</title>
</svelte:head>

<main class="chat-main" bind:this={chatMainEl}>
	<section class="explore-page container">
		{#if currentSession}
			<h2 class="chat-title">{currentSession.title}</h2>
		{/if}

		<div class="chat-history">
			{#if chatHistory.length === 0}
				<div class="empty-state">
					<p>Start typing below to begin your research.</p>
				</div>
			{/if}

			{#each chatHistory as msg, i}
				<div class="message message--{msg.role}">
					{#if msg.role === 'user'}
						<div class="user-exchange">
							<button
								class="delete-exchange"
								onclick={() => deleteExchange(i)}
								title="Delete question and answer"
							>
								<Trash2 size={13} />
							</button>
							<div class="user-bubble">
								{msg.content}
								{#if msg.filters && Object.keys(msg.filters).length > 0}
									<div class="bubble-filters">
										{#each Object.entries(msg.filters) as [key, value]}
											<span class="bubble-chip"
												><span class="bubble-chip-key">{key}</span><span class="bubble-chip-sep"
													>:</span
												>{value}</span
											>
										{/each}
									</div>
								{/if}
							</div>
						</div>
					{:else}
						<section class="klippy-answer">
							{#if msg.steps}
								<ol class="retrieval-steps" aria-label="Retrieval pipeline">
									{#each msg.steps as step}
										<li class="step" class:step--active={step.active}>
											<span class="step-mark" aria-hidden="true">
												{#if step.active}●{:else}✓{/if}
											</span>
											<span class="step-label"
												><b>{step.label}</b> — <span class="step-detail">{step.detail}</span></span
											>
											<span class="step-time"
												>{step.t != null ? `${step.t.toLocaleString()}ms` : '…'}</span
											>
										</li>
									{/each}
								</ol>
							{/if}

							<div class="answer-prose markdown-body">
								{#if msg.content}{@html marked.parse(msg.content)}{/if}
								{#if isLoading && i === chatHistory.length - 1}
									<span class="streaming-caret" aria-hidden="true"></span>
								{/if}
							</div>

							<div class="answer-actions">
								<button
									class="iconbtn"
									onclick={() => sendFeedback(true, page.params.id!)}
									title="Helpful"><ThumbsUp size={13} /></button
								>
								<button
									class="iconbtn"
									onclick={() => sendFeedback(false, page.params.id!)}
									title="Not helpful"><ThumbsDown size={13} /></button
								>
								<span class="sep"></span>
								<button
									class="iconbtn"
									onclick={() => handleSend(chatHistory[i - 1]?.content, true)}
									title="Refresh"><RotateCcw size={13} /></button
								>
								{#if msg.total_time_ms}
									<span class="answer-time"
										>{msg.total_time_ms.toLocaleString()}ms · {(
											msg.context_length ?? 0
										).toLocaleString()} chars</span
									>
								{/if}
							</div>

							{#if msg.sources?.length}
								<div class="answer-sources">
									<button
										class="sources-toggle"
										class:open={expandedSources.has(i)}
										onclick={() => toggleSources(i)}
									>
										<span>Referenced sources</span>
										<span class="sources-count">{msg.sources.length}</span>
										<ChevronDown size={12} class={expandedSources.has(i) ? 'rotated' : ''} />
									</button>
									{#if expandedSources.has(i)}
										<ul class="sources-list">
											{#each msg.sources as src, n}
												<li>
													<a href={src.url} target="_blank" rel="noopener">
														<span class="source-num">[{n + 1}]</span>
														{#if src.source === 'github'}<Code size={12} />{:else}<FileText
																size={12}
															/>{/if}
														<span class="source-title">{src.title.replace('.md', '')}</span>
														<span class="source-score">{src.score.toFixed(2)}</span>
													</a>
												</li>
											{/each}
										</ul>
									{/if}
								</div>
							{/if}
						</section>
					{/if}
				</div>
			{/each}
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

		<form
			onsubmit={(e) => {
				e.preventDefault();
				handleSend();
			}}
		>
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
					id="chat-input"
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
							document.getElementById('slider-topk')?.focus();
						}
					}}
					title="Tune search parameters"
				>
					<SlidersHorizontal size={18} />
				</button>
			</div>

			{#if showSettings}
				<div class="composer-controls" transition:slide>
					<label class="control" for="slider-topk">
						<span class="control-lbl">Top K</span>
						<input id="slider-topk" type="range" min="1" max="50" bind:value={topK} />
						<span class="control-val">{topK}</span>
					</label>
					<label class="control" for="slider-threshold">
						<span class="control-lbl">Threshold</span>
						<input
							id="slider-threshold"
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
				<span class="hint-items">
					<kbd>↵</kbd> send · <kbd>@</kbd> filter field
				</span>
				<span class="composer-meta"
					>session <b>{(page.params.id ?? '').toUpperCase().split('-')[0]}</b> · {modelName}</span
				>
			</p>
		</form>
	</div>
</section>

<style>
	/* ── Main area ──────────────────────────────── */
	.chat-main {
		flex: 1;
		position: relative;
		overflow-y: auto;
	}

	.explore-page {
		padding: var(--size-12) var(--size-6) var(--size-32);
	}

	.chat-title {
		font-family: var(--font-display);
		font-size: 1.6rem;
		font-weight: 500;
		color: var(--ink-0);
		margin-bottom: var(--size-8);
		padding-bottom: var(--size-4);
		border-bottom: 1px solid var(--border);
	}

	.chat-history {
		display: flex;
		flex-direction: column;
		gap: var(--size-6);
		max-width: 1040px;
		padding-inline: var(--size-6);
	}

	.message {
		display: flex;
		flex-direction: column;
		width: 100%;
	}

	.message--user {
		align-items: flex-end;
	}

	.message--klippy {
		align-items: flex-start;
	}

	.user-exchange {
		display: flex;
		align-items: center;
		gap: var(--size-2);
		max-width: 80%;
	}

	.delete-exchange {
		opacity: 0;
		background: none;
		border: none;
		cursor: pointer;
		padding: var(--size-1);
		color: var(--ink-2);
		transition:
			opacity 0.15s,
			color 0.15s;
		flex-shrink: 0;
	}

	.user-exchange:hover .delete-exchange {
		opacity: 1;
	}

	.delete-exchange:hover {
		color: var(--kings-red);
	}

	.user-bubble {
		background: var(--u-bg);
		color: var(--u-fg);
		padding: var(--size-4) var(--size-6);
		border-radius: 16px 16px 2px 16px;
		font-size: 1rem;
		font-weight: 300;
		box-shadow: var(--shadow-2);
	}

	.bubble-filters {
		display: flex;
		flex-wrap: nowrap;
		gap: var(--size-2);
		margin-top: var(--size-3);
		padding-top: var(--size-3);
		border-top: 1px solid color-mix(in srgb, var(--u-fg) 15%, transparent);
		overflow-x: auto;
		max-width: 100%;
		scrollbar-width: none;
	}

	.bubble-filters::-webkit-scrollbar {
		display: none;
	}

	.bubble-chip {
		font-family: var(--font-mono);
		font-size: 0.68rem;
		opacity: 0.75;
	}

	.bubble-chip-key {
		font-weight: 600;
	}

	.bubble-chip-sep {
		opacity: 0.5;
		margin: 0 1px;
	}

	.klippy-answer {
		padding: 2px 0 2px 24px;
		margin: 32px 0;
		border-left: 2px solid var(--kings-red);
		max-width: 90%;
	}

	.retrieval-steps {
		list-style: none;
		padding: 0;
		margin: 0 0 20px;
		font-family: var(--font-mono);
		font-size: 0.7rem;
		color: var(--ink-2);
	}

	.step {
		display: grid;
		grid-template-columns: 16px 1fr auto;
		gap: 10px;
		padding: 1px 0;
		align-items: center;
	}

	.step-mark {
		color: var(--teal);
		opacity: 0.85;
	}

	.step--active .step-mark {
		color: var(--kings-red);
		animation: pulse 1.1s ease-in-out infinite;
	}

	.step-label b {
		color: var(--ink-0);
		font-weight: 500;
	}

	.step-detail {
		color: var(--ink-2);
		font-size: 0.66rem;
	}

	.step-time {
		color: var(--ink-3);
		font-size: 0.62rem;
	}

	@keyframes pulse {
		50% {
			opacity: 0.2;
		}
	}

	.answer-prose {
		font-family: var(--font-display);
		font-size: 1.28rem;
		font-weight: 400;
		line-height: 1.55;
		color: var(--ink-0);
	}

	.answer-prose :global(p) {
		margin: 0 0 1em;
	}

	.answer-prose :global(strong) {
		font-weight: 600;
	}

	.answer-prose :global(code) {
		font-family: var(--font-mono);
		font-size: 0.78em;
		background: var(--kings-red-light);
		color: var(--kings-red);
		padding: 1px 6px;
		border-radius: 2px;
	}

	.streaming-caret {
		display: inline-block;
		width: 10px;
		height: 1.1em;
		vertical-align: -2px;
		background: var(--kings-red);
		opacity: 0.7;
		animation: blink 1s steps(2) infinite;
	}

	@keyframes blink {
		50% {
			opacity: 0;
		}
	}

	.answer-actions {
		display: flex;
		align-items: center;
		gap: 10px;
		margin-top: 18px;
		font-family: var(--font-mono);
		font-size: 0.64rem;
		color: var(--ink-2);
	}

	.answer-actions .iconbtn {
		border: none;
		background: transparent;
		color: var(--ink-2);
		padding: 3px;
		cursor: pointer;
		display: inline-flex;
		border-radius: 2px;
	}

	.answer-actions .iconbtn:hover {
		color: var(--kings-red);
		background: var(--kings-red-light);
	}

	.answer-actions .sep {
		width: 1px;
		height: 14px;
		background: var(--border-dark);
		margin: 0 4px;
	}

	.answer-actions .answer-time {
		margin-left: auto;
		color: var(--ink-3);
	}

	.answer-sources {
		margin-top: 18px;
		border-top: 1px dashed var(--border-dark);
		padding-top: 14px;
	}

	.sources-toggle {
		border: none;
		background: none;
		padding: 0;
		cursor: pointer;
		font-family: var(--font-mono);
		font-size: 0.64rem;
		letter-spacing: 0.12em;
		text-transform: uppercase;
		color: var(--ink-2);
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.sources-toggle:hover {
		color: var(--kings-red);
	}

	.sources-toggle .sources-count {
		color: var(--kings-red);
		letter-spacing: 0;
		font-size: 0.7rem;
	}

	.sources-toggle :global(.rotated) {
		transform: rotate(180deg);
	}

	.sources-list {
		list-style: none;
		padding: 0;
		margin: 10px 0 0;
		display: flex;
		flex-direction: column;
		gap: 1px;
	}

	.sources-list a {
		display: grid;
		grid-template-columns: 22px 16px 1fr auto;
		gap: 10px;
		align-items: center;
		padding: 7px 10px;
		border-radius: 2px;
		font-size: 0.82rem;
		color: var(--ink-1);
		text-decoration: none;
		border: 1px solid transparent;
	}

	.sources-list a:hover {
		background: var(--surface);
		border-color: var(--border);
	}

	.source-num {
		font-family: var(--font-mono);
		font-size: 0.64rem;
		color: var(--kings-red);
	}

	.source-title {
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.source-score {
		font-family: var(--font-mono);
		font-size: 0.62rem;
		color: var(--ink-3);
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

	.settings-toggle {
		background: none;
		border: none;
		cursor: pointer;
		padding: 0;
		color: var(--ink-2);
		font-family: inherit;
		font-size: inherit;
		text-transform: inherit;
		display: inline-flex;
		align-items: center;
		gap: 4px;
		transition: color 0.15s;
		margin-left: 2px;
	}

	.settings-toggle:hover {
		color: var(--kings-red);
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

	/* ── Empty state ────────────────────────────── */
	.empty-state {
		text-align: center;
		padding: 10vh 0;
		color: var(--ink-2);
		font-family: var(--font-display);
		font-size: 1.5rem;
		font-style: italic;
		opacity: 0.5;
	}

	@media (max-width: 640px) {
		.explore-page {
			padding-top: 0;
			padding-inline: var(--size-4);
		}

		.chat-history {
			padding-inline: 0;
		}

		.user-bubble {
			max-width: 100%;
			padding: var(--size-3) var(--size-4);
		}

		.klippy-answer {
			max-width: 100%;
			padding-left: var(--size-4);
			margin: 24px 0;
		}

		.retrieval-steps {
			gap: var(--size-1);
			display: flex;
			flex-direction: column;
		}

		.step {
			display: flex;
			gap: 8px;
			padding: var(--size-1) 0;
		}

		.step-label,
		.step-time {
			display: none;
		}

		.step-mark {
			font-size: 0.8rem;
		}

		.answer-prose {
			font-size: 1.15rem;
		}

		.answer-time {
			display: none;
		}

		.sources-list a {
			grid-template-columns: 22px 16px 1fr;
			padding: var(--size-3);
		}

		.source-score {
			display: none;
		}

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

		.control:first-child {
			border-right: none;
			border-bottom: 1px solid var(--border);
		}
	}
</style>
