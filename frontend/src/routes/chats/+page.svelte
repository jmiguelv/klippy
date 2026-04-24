<script lang="ts">
	import { onMount, tick } from 'svelte';
	import { slide } from 'svelte/transition';
	import { PUBLIC_API_URL } from '$env/static/public';
	import { KNOWN_FIELDS } from '$lib/filters';
	import { page } from '$app/state';
	import { marked } from 'marked';
	import {
		Plus,
		MessageSquare,
		Pencil,
		Trash2,
		ChevronLeft,
		ChevronRight,
		ChevronDown,
		ThumbsUp,
		ThumbsDown,
		RotateCcw,
		Search,
		Code,
		FileText,
		SlidersHorizontal
	} from 'lucide-svelte';

	// Types
	interface Source {
		source: string;
		url: string;
		title: string;
		score: number;
	}

	interface RetrievalStep {
		label: string;
		detail: string;
		t: number | null;
		active?: boolean;
	}

	interface Message {
		role: 'user' | 'klippy';
		content: string;
		sources?: Source[];
		steps?: RetrievalStep[];
		total_time_ms?: number;
		cached_at?: string;
		is_cached?: boolean;
		context_length?: number;
	}

	interface Session {
		id: string;
		title: string;
		messages: Message[];
		filters: Record<string, string>;
		updatedAt: number;
	}

	interface AcState {
		visible: boolean;
		mode: 'field' | 'value';
		field: string;
		partial: string;
		options: string[];
		activeIdx: number;
	}

	// State
	let sessions = $state<Session[]>([]);
	let currentSessionId = $state('');
	let query = $state('');
	let isLoading = $state(false);
	let sessionId = $state('');
	let expandedSources = $state<Set<number>>(new Set());
	let isSidebarOpen = $state(true);
	let activeFilters = $state<Record<string, string>>({});
	let topK = $state(10);
	let similarityCutoff = $state(0.3);
	let modelName = $state('...');
	let showSettings = $state(false);
	let chatMainEl: HTMLElement;

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

	function getSessionId() {
		if (typeof window === 'undefined') return '';
		if (!sessionId) {
			sessionId = localStorage.getItem('klippy_session_id') || '';
			if (!sessionId) {
				sessionId = crypto.randomUUID();
				localStorage.setItem('klippy_session_id', sessionId);
			}
		}
		return sessionId;
	}

	function toggleSources(index: number) {
		if (expandedSources.has(index)) {
			expandedSources.delete(index);
		} else {
			expandedSources.add(index);
		}
		expandedSources = new Set(expandedSources);
	}

	// Persistence
	function saveSessions() {
		if (typeof window !== 'undefined') {
			localStorage.setItem('klippy_sessions', JSON.stringify(sessions));
		}
	}

	function loadSessions() {
		if (typeof window !== 'undefined') {
			const stored = localStorage.getItem('klippy_sessions');
			if (stored) {
				sessions = JSON.parse(stored);
				sessions.sort((a, b) => b.updatedAt - a.updatedAt);
			}
		}
	}

	// CRUD
	function createNewChat(initialQuery = '') {
		const newId = crypto.randomUUID();
		const newSession: Session = {
			id: newId,
			title: initialQuery ? truncate(initialQuery, 30) : 'New Chat',
			messages: [],
			filters: {},
			updatedAt: Date.now()
		};
		sessions = [newSession, ...sessions];
		currentSessionId = newId;
		activeFilters = {};
		expandedSources = new Set();
		saveSessions();
		return newId;
	}

	function deleteChat(id: string, e: Event) {
		e.stopPropagation();
		if (!confirm('Are you sure you want to delete this chat?')) return;
		sessions = sessions.filter((s) => s.id !== id);
		if (currentSessionId === id) {
			currentSessionId = sessions[0]?.id || '';
			activeFilters = sessions[0]?.filters ?? {};
		}
		saveSessions();
	}

	function renameChat(id: string, e: Event) {
		e.stopPropagation();
		const session = sessions.find((s) => s.id === id);
		if (!session) return;
		const newTitle = prompt('Rename chat:', session.title);
		if (newTitle && newTitle.trim()) {
			session.title = newTitle.trim();
			session.updatedAt = Date.now();
			saveSessions();
		}
	}

	function selectChat(id: string) {
		currentSessionId = id;
		activeFilters = sessions.find((s) => s.id === id)?.filters ?? {};
		expandedSources = new Set();
	}

	function deleteExchange(i: number) {
		const sIdx = sessions.findIndex((s) => s.id === currentSessionId);
		if (sIdx === -1) return;
		sessions[sIdx].messages = sessions[sIdx].messages.filter(
			(_, idx) => idx !== i && idx !== i + 1
		);
		saveSessions();
	}

	function truncate(str: string, n: number) {
		return str.length > n ? str.slice(0, n - 1) + '...' : str;
	}

	function parseFilters(raw: string): { text: string; filters: Record<string, string> } {
		const filters: Record<string, string> = {};
		// Matches @field:"quoted value" or @field:unquoted
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
		// Sync session
		const sIdx = sessions.findIndex((s) => s.id === currentSessionId);
		if (sIdx !== -1) {
			sessions[sIdx].filters = activeFilters;
			saveSessions();
		}
	}

	// ── Autocomplete ────────────────────────────────────────────

	const AC_CACHE_TTL_MS = 3_600_000; // 1 hour
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
		} catch { /* ignore parse errors */ }

		try {
			const res = await fetch(`${PUBLIC_API_URL}/debug/stats/all`);
			const data = await res.json() as Record<string, Record<string, number>>;
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
		// Fallback: fetch individual field stats if bulk cache missed this field
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
		// If the bulk fetch is still in flight, wait for it before falling back to
		// individual per-field requests (which would each hit Qdrant on a cold cache).
		if (acCache[field] === undefined && allStatsReady) await allStatsReady;
		const values = acCache[field] !== undefined ? acCache[field] : await fetchValues(field);
		const options = values.filter((v) => v.toLowerCase().includes(partial.toLowerCase()));
		ac = { visible: options.length > 0, mode: 'value', field, partial, options, activeIdx: 0 };
	}

	async function handleInput(e: Event) {
		const input = e.target as HTMLInputElement;
		const before = input.value.slice(0, input.selectionStart ?? input.value.length);

		const valueMatch = before.match(/@(\w+):(\w*)$/);
		const fieldMatch = !valueMatch && before.match(/@(\w*)$/);

		if (valueMatch) {
			const [, field, partial] = valueMatch;
			if (acCache[field] !== undefined) {
				await showValueOptions(field, partial);
			} else {
				await fetchValues(field);
				// Re-read cursor state after async gap
				const inputEl = e.target as HTMLInputElement;
				const nowBefore = inputEl.value.slice(0, inputEl.selectionStart ?? inputEl.value.length);
				const nowMatch = nowBefore.match(/@(\w+):(\w*)$/);
				if (nowMatch && nowMatch[1] === field) {
					await showValueOptions(field, nowMatch[2]);
				}
			}
		} else if (fieldMatch) {
			const [, partial] = fieldMatch;
			const options = KNOWN_FIELDS.filter((f) => f.toLowerCase().includes(partial.toLowerCase()));
			ac = { visible: options.length > 0, mode: 'field', field: '', partial, options, activeIdx: 0 };
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
			// Auto-quote values that contain spaces
			const quotedOpt = opt.includes(' ') ? `"${opt}"` : opt;
			query = query.replace(new RegExp(`@${ac.field}:(?:"[^"]*"|\\S*)$`), `@${ac.field}:${quotedOpt} `);
			ac = { ...ac, visible: false };
			document.getElementById('chat-input')?.focus();
		}
	}

	// ── Send ────────────────────────────────────────────────────

	async function sendFeedback(isPositive: boolean, sId: string) {
		try {
			await fetch(`${PUBLIC_API_URL}/feedback`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ session_id: sId, is_positive: isPositive })
			});
			if (!isPositive) {
				alert('Session history cleared on server. Starting fresh!');
				const sIdx = sessions.findIndex((s) => s.id === sId);
				if (sIdx !== -1) {
					sessions[sIdx].messages = [];
					saveSessions();
				}
			}
		} catch (e) {
			console.error(e);
		}
	}

	async function handleSend(textOverride?: string, isRefresh = false) {
		const raw = textOverride || query.trim();
		if (!raw) return;

		// Parse @field:value tokens and merge into active filters
		const { text, filters: parsed } = parseFilters(raw);
		activeFilters = { ...activeFilters, ...parsed };
		ac = { ...ac, visible: false };

		if (!currentSessionId) createNewChat(text);
		if (!textOverride) {
			// Keep only the filter tokens in the query input
			const filterMatches = raw.match(/@\w+:(?:"[^"]+"|\S+)/g) || [];
			query = filterMatches.join(' ') + (filterMatches.length > 0 ? ' ' : '');
		}

		const sIdx = sessions.findIndex((s) => s.id === currentSessionId);
		if (sIdx === -1) return;

		if (sessions[sIdx].messages.length === 0) {
			sessions[sIdx].title = truncate(text, 35);
		}

		// Persist current filters on the session
		sessions[sIdx].filters = { ...activeFilters };

		if (!isRefresh) {
			sessions[sIdx].messages = [...sessions[sIdx].messages, { role: 'user', content: text }];
			await tick();
			chatMainEl?.scrollTo({ top: chatMainEl.scrollHeight, behavior: 'smooth' });
		}
		sessions[sIdx].updatedAt = Date.now();

		isLoading = true;

		if (isRefresh) {
			await fetch(`${PUBLIC_API_URL}/feedback`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ session_id: currentSessionId, is_positive: false })
			});
		}

		const startTime = Date.now();
		// Add a placeholder message immediately so streaming renders in place
		const streamingMessage: Message = {
			role: 'klippy',
			content: '',
			steps: [
				{
					label: 'Parsing query',
					detail: Object.keys(parsed).length > 0 ? `extracted ${Object.keys(parsed).length} filters` : 'no explicit filters',
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
			sessions[sIdx].messages[sessions[sIdx].messages.length - 1] = streamingMessage;
		} else {
			sessions[sIdx].messages = [...sessions[sIdx].messages, streamingMessage];
		}
		const msgIdx = sessions[sIdx].messages.length - 1;

		await tick();
		chatMainEl?.scrollTo({ top: chatMainEl.scrollHeight, behavior: 'smooth' });

		try {
			const response = await fetch(`${PUBLIC_API_URL}/query-stream`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					text,
					session_id: currentSessionId,
					filters: activeFilters,
					top_k: topK,
					similarity_cutoff: similarityCutoff > 0 ? similarityCutoff : null
				})
			});

			if (!response.ok || !response.body) throw new Error(`HTTP ${response.status}`);

			const reader = response.body.getReader();
			const decoder = new TextDecoder();
			let buffer = '';
			let hasStartedSynthesis = false;

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
						const steps = sessions[sIdx].messages[msgIdx].steps || [];
						// Finish "Searching Qdrant" (index 1)
						if (steps[1]) {
							steps[1].active = false;
							steps[1].t = searchTime;
						}

						// Push "Retrieved N chunks" (index 2)
						const numSources = evt.num_sources || 0;
						steps.push({
							label: `Retrieved ${numSources} chunk${numSources === 1 ? '' : 's'}`,
							detail: 'Ranked by semantic relevance',
							t: searchTime,
							active: false
						});

						// Push "Synthesising" (index 3)
						steps.push({
							label: 'Synthesising',
							detail: 'Reasoning across retrieved chunks',
							t: null,
							active: true
						});
						sessions[sIdx].messages[msgIdx].steps = steps;
						// Trigger reactivity
						sessions[sIdx].messages[msgIdx] = { ...sessions[sIdx].messages[msgIdx] };
					} else if (evt.type === 'chunk') {
						sessions[sIdx].messages[msgIdx] = {
							...sessions[sIdx].messages[msgIdx],
							content: sessions[sIdx].messages[msgIdx].content + evt.text
						};
						await tick();
						chatMainEl?.scrollTo({ top: chatMainEl.scrollHeight, behavior: 'smooth' });
					} else if (evt.type === 'done') {
						const totalTime = Date.now() - startTime;
						const steps = sessions[sIdx].messages[msgIdx].steps || [];

						// Finish "Synthesising" (index 3)
						if (steps[3]) {
							steps[3].active = false;
							steps[3].t = totalTime - (steps[1]?.t || 0);
						}

						sessions[sIdx].messages[msgIdx] = {
							...sessions[sIdx].messages[msgIdx],
							steps,
							sources: evt.sources,
							total_time_ms: evt.total_time_ms,
							cached_at: evt.cached_at,
							context_length: evt.context_length
						};
					} else if (evt.type === 'error') {
						sessions[sIdx].messages[msgIdx] = {
							...sessions[sIdx].messages[msgIdx],
							content: `Error: ${evt.detail}`
						};
					}
				}
			}

			sessions[sIdx].updatedAt = Date.now();
			saveSessions();
		} catch (e) {
			console.error(e);
			sessions[sIdx].messages[msgIdx] = {
				...sessions[sIdx].messages[msgIdx],
				content: 'Error: Could not connect to the research engine.'
			};
			saveSessions();
		} finally {
			isLoading = false;
			await tick();
			chatMainEl?.scrollTo({ top: chatMainEl.scrollHeight, behavior: 'smooth' });
		}
	}

	// Derived
	let currentSession = $derived(sessions.find((s) => s.id === currentSessionId));
	let chatHistory = $derived(currentSession?.messages || []);
	let hasFilters = $derived(Object.keys(activeFilters).length > 0);

	onMount(() => {
		loadSessions();
		getSessionId();
		if (sessions.length > 0 && !currentSessionId) {
			currentSessionId = sessions[0].id;
			activeFilters = sessions[0].filters ?? {};
		}
		allStatsReady = fetchAllStats();

		const savedModel = localStorage.getItem('klippy_model_name');
		if (savedModel) {
			modelName = savedModel;
		}

		// Handle query forwarded from home page — consume once and clear URL
		const q = new URLSearchParams(window.location.search).get('q');
		if (q) {
			history.replaceState({}, '', window.location.pathname);
			createNewChat(q);
			handleSend(q);
		}
	});
</script>

<svelte:head>
	<title>Chats — Klippy Chat</title>
</svelte:head>

<div class="chat-layout">
	<aside class="sidebar" class:closed={!isSidebarOpen}>
		<header class="sidebar-header">
			<div class="wordmark-wrap">
				<span class="sidebar-wordmark">Chats</span>
			</div>
			<button class="new-chat-btn" onclick={() => createNewChat()}>
				<Plus size={16} />
				<span>New Chat</span>
			</button>
		</header>

		<div class="session-list">
			{#each sessions as s}
				<div
					role="button"
					tabindex="0"
					class="session-item"
					class:active={currentSessionId === s.id}
					onclick={() => selectChat(s.id)}
					onkeydown={(e) => e.key === 'Enter' && selectChat(s.id)}
				>
					<MessageSquare class="session-icon" size={14} />
					<span class="session-title">{s.title}</span>
					<div class="session-actions">
						<button onclick={(e) => renameChat(s.id, e)} title="Rename"><Pencil size={12} /></button>
						<button onclick={(e) => deleteChat(s.id, e)} title="Delete"><Trash2 size={12} /></button>
					</div>
				</div>
			{/each}
		</div>
	</aside>

	<div class="chat-content">
		<button
			class="sidebar-toggle"
			onclick={() => (isSidebarOpen = !isSidebarOpen)}
			title="Toggle Sidebar"
		>
			{#if isSidebarOpen}<ChevronLeft size={14} />{:else}<ChevronRight size={14} />{/if}
		</button>

		<main class="chat-main" bind:this={chatMainEl}>

		<section class="explore-page container">
			{#if currentSession}
				<h2 class="chat-title">{currentSession.title}</h2>
			{/if}

			<div class="chat-history">
				{#if !currentSessionId && sessions.length === 0}
					<div class="empty-state">
						<p>Start a new conversation to begin research.</p>
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
												<span class="step-label"><b>{step.label}</b> — <span class="step-detail">{step.detail}</span></span>
												<span class="step-time">{step.t ? `${step.t}ms` : '…'}</span>
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
									<button class="iconbtn" onclick={() => sendFeedback(true, currentSessionId)} title="Helpful"><ThumbsUp size={13}/></button>
									<button class="iconbtn" onclick={() => sendFeedback(false, currentSessionId)} title="Not helpful"><ThumbsDown size={13}/></button>
									<span class="sep"></span>
									<button class="iconbtn" onclick={() => handleSend(chatHistory[i-1]?.content, true)} title="Refresh"><RotateCcw size={13}/></button>
									{#if msg.total_time_ms}
										<span class="answer-time">{msg.total_time_ms.toLocaleString()}ms · {Math.round((msg.context_length ?? 0) / 1000)}k chars</span>
									{/if}
								</div>

								{#if msg.sources?.length}
									<div class="answer-sources">
										<button class="sources-toggle" class:open={expandedSources.has(i)} onclick={() => toggleSources(i)}>
											<span>Referenced sources</span>
											<span class="sources-count">{msg.sources.length}</span>
											<ChevronDown size={12} class={expandedSources.has(i) ? 'rotated' : ''}/>
										</button>
										{#if expandedSources.has(i)}
											<ul class="sources-list">
												{#each msg.sources as src, n}
													<li>
														<a href={src.url} target="_blank" rel="noopener">
															<span class="source-num">[{n + 1}]</span>
															{#if src.source === 'github'}<Code size={12}/>{:else}<FileText size={12}/>{/if}
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
				<!-- Autocomplete dropdown — anchored above the form -->
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

				<form onsubmit={(e) => { e.preventDefault(); handleSend(); }}>
					<div class="composer-input">
						<input
							id="chat-input"
							type="text"
							bind:value={query}
							placeholder="Ask Klippy… use @ to filter by field"
							autocomplete="off"
							oninput={handleInput}
							onkeydown={handleKeydown}
							onblur={() => setTimeout(() => (ac = { ...ac, visible: false }), 150)}
						/>
					</div>

					{#if showSettings}
						<div class="composer-controls" transition:slide>
							<label class="control">
								<span class="control-lbl">Top K</span>
								<input type="range" min="1" max="50" bind:value={topK}/>
								<span class="control-val">{topK}</span>
							</label>
							<label class="control">
								<span class="control-lbl">Threshold</span>
								<input type="range" min="0" max="1" step="0.05" bind:value={similarityCutoff}/>
								<span class="control-val">{similarityCutoff.toFixed(2)}</span>
							</label>
						</div>
					{/if}

					<p class="composer-hint">
						<span class="hint-items">
							<kbd>↵</kbd> send · <kbd>@</kbd> filter field ·
							<button type="button" class="settings-toggle" onclick={() => showSettings = !showSettings}>
								<SlidersHorizontal size={12} /> {showSettings ? 'Hide' : 'Tune'}
							</button>
						</span>
						<span class="composer-meta">session <b>{currentSessionId.toUpperCase().split('-')[0]}</b> · {modelName}</span>
					</p>
				</form>
		</div>
	</section>
	</div>
</div>

<style>
	.chat-layout {
		display: flex;
		height: calc(100vh - 59px);
		overflow: hidden;
		background: var(--canvas);
	}

	/* ── Sidebar ────────────────────────────────── */
	.sidebar {
		width: 280px;
		background: var(--surface);
		border-right: 1px solid var(--border);
		display: flex;
		flex-direction: column;
		transition:
			transform 0.3s ease,
			margin-left 0.3s ease;
	}

	.sidebar.closed {
		margin-left: -280px;
	}

	.sidebar-header {
		padding: var(--size-4);
		display: flex;
		flex-direction: column;
		gap: var(--size-4);
		border-bottom: 1px solid var(--border);
	}

	.wordmark-wrap {
		padding: 0 var(--size-2);
	}

	.sidebar-wordmark {
		font-family: var(--font-display);
		font-size: 1.4rem;
		font-weight: 600;
		color: var(--ink-0);
		letter-spacing: 0.02em;
	}

	.new-chat-btn {
		width: 100%;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 8px;
		padding: 10px;
		background: var(--surface);
		border: 1px dashed var(--kings-red);
		color: var(--kings-red);
		border-radius: 4px;
		font-family: var(--font-sans);
		font-size: 0.85rem;
		font-weight: 500;
		cursor: pointer;
		transition: background 0.15s;
	}

	.new-chat-btn:hover {
		background: var(--kings-red-light);
	}

	.session-list {
		flex: 1;
		overflow-y: auto;
		padding: var(--size-2);
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.session-item {
		display: flex;
		align-items: center;
		gap: var(--size-2);
		padding: var(--size-2) var(--size-3);
		background: none;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		text-align: left;
		transition: background 0.15s;
		position: relative;
	}

	.session-item:hover {
		background: var(--canvas);
	}

	.session-item.active {
		border-left: 2px solid var(--kings-red);
		color: var(--kings-red);
		border-radius: 0 4px 4px 0;
	}

	.session-icon {
		opacity: 0.4;
		flex-shrink: 0;
	}

	.session-title {
		font-size: 0.85rem;
		font-weight: 400;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		flex: 1;
	}

	.session-actions {
		display: none;
		gap: 4px;
	}

	.session-item:hover .session-actions {
		display: flex;
	}

	.session-actions button {
		background: none;
		border: none;
		cursor: pointer;
		font-size: 0.8rem;
		padding: 2px;
		opacity: 0.6;
	}

	.session-actions button:hover {
		opacity: 1;
	}

	/* ── Main Chat Area ─────────────────────────── */
	.chat-content {
		flex: 1;
		display: flex;
		flex-direction: column;
		overflow: hidden;
		position: relative;
	}

	.chat-main {
		flex: 1;
		position: relative;
		overflow-y: auto;
	}

	.sidebar-toggle {
		position: absolute;
		top: 20px;
		left: 20px;
		z-index: 110;
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: 4px;
		width: 32px;
		height: 32px;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.7rem;
		color: var(--ink-2);
		box-shadow: var(--shadow-2);
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
		position: relative;
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

	/* Custom Range Input */
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
		z-index: 200;
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

	.empty-state {
		text-align: center;
		padding: 10vh 0;
		color: var(--ink-2);
		font-family: var(--font-display);
		font-size: 1.5rem;
		font-style: italic;
		opacity: 0.5;
	}

	@media (max-width: 768px) {
		.sidebar {
			position: fixed;
			height: 100%;
			z-index: 200;
		}

		.sidebar.closed {
			transform: translateX(-100%);
		}
	}
</style>
