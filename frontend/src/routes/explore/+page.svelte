<script lang="ts">
	import { onMount, tick } from 'svelte';
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
		FileText
	} from 'lucide-svelte';

	// Types
	interface Source {
		source: string;
		url: string;
		title: string;
		score: number;
	}

	interface Message {
		role: 'user' | 'klippy';
		content: string;
		sources?: Source[];
		total_time_ms?: number;
		cached_at?: string;
		is_cached?: boolean;
		context_length?: number;
	}

	interface Session {
		id: string;
		title: string;
		messages: Message[];
		updatedAt: number;
	}

	// State (Svelte 5 Runes)
	let sessions = $state<Session[]>([]);
	let currentSessionId = $state('');
	let query = $state('');
	let isLoading = $state(false);
	let loaderVerb = $state('Synthesising');
	let sessionId = $state('');
	let expandedSources = $state<Set<number>>(new Set());
	let isSidebarOpen = $state(true);
	let activeFilters = $state<Record<string, string>>({});
	let chatMainEl: HTMLElement;

	const LOADER_VERBS = [
		'Synthesising',
		'Retrieving',
		'Collating',
		'Indexing',
		'Reasoning',
		'Cross-referencing',
		'Hermeneuticising',
		'Lemmatising'
	];

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
		expandedSources = new Set(expandedSources); // Trigger update
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
			updatedAt: Date.now()
		};
		sessions = [newSession, ...sessions];
		currentSessionId = newId;
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
		const text = raw
			.replace(/@(\w+):(\S+)/g, (_, k, v) => {
				filters[k] = v;
				return '';
			})
			.trim();
		return { text, filters };
	}

	function removeFilter(key: string) {
		const { [key]: _, ...rest } = activeFilters;
		activeFilters = rest;
		query = query.replace(new RegExp(`@${key}:\\S+\\s*`, 'g'), '').trim();
	}

	async function sendFeedback(isPositive: boolean, sId: string) {
		try {
			await fetch('http://localhost:8000/feedback', {
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
		const { text, filters } = parseFilters(raw);
		activeFilters = filters;

		if (!currentSessionId) createNewChat(text);

		if (!textOverride) query = '';
		const sIdx = sessions.findIndex((s) => s.id === currentSessionId);
		if (sIdx === -1) return;

		if (sessions[sIdx].messages.length === 0) {
			sessions[sIdx].title = truncate(text, 35);
		}

		if (!isRefresh) {
			sessions[sIdx].messages = [...sessions[sIdx].messages, { role: 'user', content: text }];
			await tick();
			chatMainEl?.scrollTo({ top: chatMainEl.scrollHeight, behavior: 'smooth' });
		}
		sessions[sIdx].updatedAt = Date.now();

		isLoading = true;
		let verbIndex = 0;
		const interval = setInterval(() => {
			loaderVerb = LOADER_VERBS[++verbIndex % LOADER_VERBS.length];
		}, 2000);

		if (isRefresh) {
			await fetch('http://localhost:8000/feedback', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ session_id: currentSessionId, is_positive: false })
			});
		}

		try {
			const response = await fetch('http://localhost:8000/query', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ text, session_id: currentSessionId, filters })
			});
			const data = await response.json();

			const newMessage: Message = {
				role: 'klippy',
				content: data.answer,
				sources: data.sources,
				total_time_ms: data.total_time_ms,
				cached_at: data.cached_at,
				is_cached: data.cached,
				context_length: data.context_length
			};

			if (isRefresh) {
				sessions[sIdx].messages[sessions[sIdx].messages.length - 1] = newMessage;
			} else {
				sessions[sIdx].messages = [...sessions[sIdx].messages, newMessage];
			}
			sessions[sIdx].updatedAt = Date.now();
			saveSessions();
		} catch (e) {
			console.error(e);
			sessions[sIdx].messages = [
				...sessions[sIdx].messages,
				{ role: 'klippy', content: 'Error: Could not connect to the research engine.' }
			];
			saveSessions();
		} finally {
			clearInterval(interval);
			isLoading = false;
			await tick();
			chatMainEl?.scrollTo({ top: chatMainEl.scrollHeight, behavior: 'smooth' });
		}
	}

	// Derived
	let currentSession = $derived(sessions.find((s) => s.id === currentSessionId));
	let chatHistory = $derived(currentSession?.messages || []);

	// Svelte 5 Effect for URL parameters
	$effect(() => {
		const q = page.url.searchParams.get('q');
		if (q && sessions.length === 0 && !isLoading) {
			handleSend(q);
		}
	});

	onMount(() => {
		loadSessions();
		getSessionId();
		if (sessions.length > 0 && !currentSessionId) {
			currentSessionId = sessions[0].id;
		}
	});
</script>

<svelte:head>
	<title>Explore — Klippy Chat</title>
</svelte:head>

<div class="chat-layout">
	<aside class="sidebar" class:closed={!isSidebarOpen}>
		<header class="sidebar-header">
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
						<button onclick={(e) => renameChat(s.id, e)} title="Rename"><Pencil size={12} /></button
						>
						<button onclick={(e) => deleteChat(s.id, e)} title="Delete"><Trash2 size={12} /></button
						>
					</div>
				</div>
			{/each}
		</div>
	</aside>

	<main class="chat-main" bind:this={chatMainEl}>
		<button
			class="sidebar-toggle"
			onclick={() => (isSidebarOpen = !isSidebarOpen)}
			title="Toggle Sidebar"
		>
			{#if isSidebarOpen}<ChevronLeft size={14} />{:else}<ChevronRight size={14} />{/if}
		</button>

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
							<article class="klippy-card">
								<header class="card-meta">
									<div class="meta-left">
										<span class="query-label">Klippy</span>
										{#if msg.is_cached}
											<span class="badge badge--cached">⚡ Cached</span>
										{/if}
										{#if msg.context_length}
											<span class="badge badge--context" title="Consumed context length">
												{Math.round(msg.context_length / 1000)}k chars
											</span>
										{/if}
									</div>
									<div class="meta-right">
										<div class="actions">
											<button
												class="icon-btn"
												onclick={() => sendFeedback(true, currentSessionId)}
												title="Helpful"
											>
												<ThumbsUp size={14} />
											</button>
											<button
												class="icon-btn"
												onclick={() => sendFeedback(false, currentSessionId)}
												title="Not helpful"
											>
												<ThumbsDown size={14} />
											</button>
											<div class="sep"></div>
											<button
												class="icon-btn"
												onclick={() => handleSend(chatHistory[i - 1]?.content, true)}
												title="Refresh"
											>
												<RotateCcw size={14} />
											</button>
										</div>
										{#if msg.total_time_ms}
											<span class="timing">{msg.total_time_ms.toLocaleString()}ms</span>
										{/if}
									</div>
								</header>

								<div class="card-content markdown-body">
									{#if msg.content}
										{@html marked.parse(msg.content)}
									{:else}
										<p>No content available.</p>
									{/if}
								</div>
								{#if msg.sources && msg.sources.length > 0}
									<footer class="card-footer">
										<button class="toggle-btn" onclick={() => toggleSources(i)}>
											<span class="toggle-label">Referenced Sources</span>
											<ChevronDown
												size={14}
												class={expandedSources.has(i) ? 'toggle-icon rotated' : 'toggle-icon'}
											/>
										</button>
										{#if expandedSources.has(i)}
											<div class="sources-grid">
												{#each msg.sources as src}
													<a href={src.url} target="_blank" rel="noopener" class="source-link">
														{#if src.source === 'github'}
															<Code size={13} />
														{:else}
															<FileText size={13} />
														{/if}
														<span>{src.title.replace('.md', '')}</span>
													</a>
												{/each}
											</div>
										{/if}
									</footer>
								{/if}
							</article>
						{/if}
					</div>
				{/each}
			</div>
		</section>

		<section class="query-area">
			<div class="container query-container">
				{#if isLoading}
					<p class="loader-verb">{loaderVerb}…</p>
				{/if}
				<form
					class="query-box"
					class:loading={isLoading}
					onsubmit={(e) => {
						e.preventDefault();
						handleSend();
					}}
				>
					{#if isLoading}
						<div class="loading-rail" aria-hidden="true"></div>
					{/if}
					<p class="query-label">Ask Klippy</p>
					{#if Object.keys(activeFilters).length > 0}
						<div class="filter-chips">
							{#each Object.entries(activeFilters) as [k, v]}
								<span class="chip">
									<span class="chip-key">{k}</span>
									<span class="chip-sep">:</span>
									<span class="chip-val">{v}</span>
									<button type="button" class="chip-remove" onclick={() => removeFilter(k)}>×</button>
								</span>
							{/each}
						</div>
					{/if}
					<div class="query-input-row">
						<input
							id="chat-input"
							type="text"
							bind:value={query}
							placeholder="Follow up or ask something new..."
							autocomplete="off"
						/>
						<button type="submit" class="btn-primary" disabled={isLoading}>
							<Search size={16} />
							<span>Send</span>
						</button>
					</div>
					<p class="query-hint">Press <kbd>↵ Enter</kbd> to send</p>
				</form>
			</div>
		</section>
	</main>
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
		border-bottom: 1px solid var(--border);
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
		background: var(--kings-red-light);
		color: var(--kings-red);
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
	.chat-main {
		flex: 1;
		display: flex;
		flex-direction: column;
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
		background: var(--ink-1);
		color: white;
		padding: var(--size-4) var(--size-6);
		border-radius: 16px 16px 2px 16px;
		font-size: 1rem;
		font-weight: 300;
		box-shadow: var(--shadow-2);
	}

	.klippy-card {
		background: var(--surface);
		border: 1px solid var(--border);
		border-left: 4px solid var(--kings-red);
		box-shadow: var(--shadow-subtle);
		max-width: 90%;
	}

	.card-meta {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: var(--size-4) var(--size-6);
		border-bottom: 1px solid var(--border);
		background: var(--canvas);
	}

	.meta-left,
	.meta-right {
		display: flex;
		align-items: center;
		gap: var(--size-4);
	}

	.badge {
		font-family: var(--font-mono);
		font-size: 0.6rem;
		padding: 2px var(--size-2);
		border: 1px solid;
		border-radius: 2px;
		text-transform: uppercase;
	}
	.badge--cached {
		color: var(--teal);
		border-color: var(--teal);
		background: var(--teal-light);
	}
	.badge--context {
		color: var(--ink-2);
		border-color: var(--border-dark);
	}

	.actions {
		display: flex;
		gap: var(--size-2);
	}
	.icon-btn {
		background: none;
		border: 1px solid var(--border);
		border-radius: 4px;
		cursor: pointer;
		padding: 4px;
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--ink-2);
		opacity: 0.5;
		transition: all 0.15s;
		text-shadow: none;
	}
	.icon-btn:hover {
		opacity: 1;
		background: var(--kings-red-light);
		border-color: var(--kings-red);
		color: var(--kings-red);
	}

	.card-content {
		padding: var(--size-6);
		font-family: var(--font-sans);
		font-size: 0.95rem;
		line-height: 1.7;
	}

	.card-footer {
		border-top: 1px solid var(--border);
		background: var(--canvas);
	}
	.toggle-btn {
		width: 100%;
		display: flex;
		justify-content: space-between;
		padding: var(--size-4) var(--size-6);
		background: none;
		border: none;
		cursor: pointer;
		transition: background 0.1s;
		text-shadow: none;
	}
	.toggle-btn:hover {
		background: rgba(0, 0, 0, 0.02);
	}
	.toggle-label {
		font-family: var(--font-mono);
		font-size: 0.7rem;
		text-transform: uppercase;
		color: var(--ink-2);
		letter-spacing: 0.08em;
	}
	.toggle-icon {
		transition: transform 0.2s;
		color: var(--ink-2);
	}
	.rotated {
		transform: rotate(180deg);
	}

	.sources-grid {
		display: flex;
		flex-wrap: wrap;
		gap: var(--size-3);
		padding: 0 var(--size-6) var(--size-6);
	}
	.source-link {
		display: inline-flex;
		align-items: center;
		gap: 8px;
		padding: 5px 12px;
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: 4px;
		font-size: 0.8rem;
		color: var(--ink-1);
		transition: all 0.15s;
		text-shadow: none;
	}
	.source-link:hover {
		border-color: var(--kings-red);
		color: var(--kings-red);
		transform: translateY(-1px);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
	}

	.query-area {
		position: sticky;
		bottom: 0;
		background: linear-gradient(transparent, var(--canvas) 30%);
		padding: var(--size-6) 0;
		z-index: 100;
	}

	#chat-input {
		flex: 1;
		border: none;
		outline: none;
		padding: var(--size-2) 0;
		font-size: 1.1rem;
		font-family: var(--font-sans);
		font-weight: 300;
		background: transparent;
		color: var(--ink-0);
	}

	/* ── Loading state: animate the query box border-top ── */
	.query-box {
		position: relative;
	}

	.query-box.loading {
		border-top-color: var(--border-dark);
	}

	.loading-rail {
		position: absolute;
		top: -4px;
		left: 0;
		right: 0;
		height: 4px;
		overflow: hidden;
		pointer-events: none;
	}

	.loading-rail::after {
		content: '';
		position: absolute;
		top: 0;
		left: -35%;
		width: 35%;
		height: 100%;
		background: var(--kings-red);
		animation: border-scan 1.3s linear infinite;
	}

	@keyframes border-scan {
		from {
			left: -35%;
		}
		to {
			left: 100%;
		}
	}

	.filter-chips {
		display: flex;
		flex-wrap: wrap;
		gap: var(--size-2);
	}

	.chip {
		display: inline-flex;
		align-items: center;
		gap: 2px;
		font-family: var(--font-mono);
		font-size: 0.65rem;
		background: var(--kings-red-light);
		color: var(--kings-red);
		border: 1px solid var(--kings-red);
		border-radius: 3px;
		padding: 2px var(--size-2);
	}

	.chip-key {
		font-weight: 600;
	}

	.chip-sep {
		opacity: 0.5;
	}

	.chip-remove {
		background: none;
		border: none;
		cursor: pointer;
		color: inherit;
		padding: 0 0 0 var(--size-1);
		font-size: 0.8rem;
		line-height: 1;
		opacity: 0.6;
	}

	.chip-remove:hover {
		opacity: 1;
	}

	.loader-verb {
		font-family: var(--font-mono);
		font-size: 0.75rem;
		color: var(--ink-2);
		letter-spacing: 0.08em;
		text-align: left;
		margin-bottom: var(--size-2);
		animation: fade-cycle 2s ease-in-out infinite;
	}

	@keyframes fade-cycle {
		0%,
		100% {
			opacity: 0.5;
		}
		50% {
			opacity: 1;
		}
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
