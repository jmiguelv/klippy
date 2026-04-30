<script lang="ts">
	import { onMount, tick, untrack } from 'svelte';
	import { PUBLIC_API_URL } from '$env/static/public';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { chatState } from '$lib/chat-state.svelte';
	import { marked } from 'marked';
	import Composer from '$lib/Composer.svelte';
	import {
		Trash2,
		ChevronDown,
		ThumbsUp,
		ThumbsDown,
		RotateCcw,
		Code,
		FileText
	} from 'lucide-svelte';

	// Per-session UI state — reset when params.id changes
	let expandedSources = $state<Set<number>>(new Set());
	let activeFilters = $state<Record<string, string>>({});
	let isLoading = $state(false);
	let modelName = $state('...');
	let chatMainEl: HTMLElement;

	// Reset per-session state when navigating between sessions
	$effect(() => {
		const id = page.params.id;
		const session = untrack(() => chatState.sessions.find((s) => s.id === id));
		activeFilters = session?.filters ? { ...session.filters } : {};
		expandedSources = new Set();
	});

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
		const raw = textOverride?.trim();
		if (!raw && !isRefresh) return;

		// If we have a textOverride (from URL or Refresh), parse it for filters.
		// If it comes from Composer, filters are already in activeFilters.
		if (raw) {
			const { text, filters: parsed } = parseFilters(raw);
			activeFilters = { ...activeFilters, ...parsed };
			// We use the cleaned text for the actual query
			processSend(text, isRefresh);
		} else if (isRefresh) {
			// Refresh uses the previous message content which should already be clean text
			const sIdx = chatState.sessions.findIndex((s) => s.id === page.params.id);
			const lastUserMsg = chatState.sessions[sIdx].messages[chatState.sessions[sIdx].messages.length - 2];
			if (lastUserMsg) {
				processSend(lastUserMsg.content, true);
			}
		}
	}

	async function processSend(text: string, isRefresh: boolean) {
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
					detail: `top_k=${chatState.topK} · threshold=${chatState.threshold.toFixed(2)}`,
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
					top_k: chatState.topK,
					similarity_cutoff: chatState.threshold > 0 ? chatState.threshold : null
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

	onMount(() => {
		chatState.loadSessions();
		const session = chatState.sessions.find((s) => s.id === page.params.id);
		if (!session) {
			goto('/');
			return;
		}

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
		<Composer
			onSend={(text) => processSend(text, false)}
			bind:activeFilters
		/>
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
		z-index: var(--z-nav);
		overflow: visible;
	}

	.composer .container {
		position: relative;
		overflow: visible;
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
	}
</style>

