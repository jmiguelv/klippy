<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { marked } from 'marked';

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
	let expandedSources = $state<Set<number>>(new Set()); // Track expanded state for each message
	let isSidebarOpen = $state(true);

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

	function truncate(str: string, n: number) {
		return str.length > n ? str.slice(0, n - 1) + '...' : str;
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
				const sIdx = sessions.findIndex(s => s.id === sId);
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
		const text = textOverride || query.trim();
		if (!text) return;

		if (!currentSessionId) createNewChat(text);

		if (!textOverride) query = '';
		const sIdx = sessions.findIndex((s) => s.id === currentSessionId);
		if (sIdx === -1) return;

		if (sessions[sIdx].messages.length === 0) {
			sessions[sIdx].title = truncate(text, 35);
		}

		if (!isRefresh) {
			sessions[sIdx].messages = [...sessions[sIdx].messages, { role: 'user', content: text }];
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
				body: JSON.stringify({ text, session_id: currentSessionId })
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
			sessions[sIdx].messages = [...sessions[sIdx].messages, { role: 'klippy', content: 'Error: Could not connect to the research engine.' }];
		} finally {
			clearInterval(interval);
			isLoading = false;
			setTimeout(() => window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' }), 100);
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
				<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
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
					<svg class="session-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
					<span class="session-title">{s.title}</span>
					<div class="session-actions">
						<button onclick={(e) => renameChat(s.id, e)} title="Rename">✏️</button>
						<button onclick={(e) => deleteChat(s.id, e)} title="Delete">🗑️</button>
					</div>
				</div>
			{/each}
		</div>
	</aside>

	<main class="chat-main">
		<button class="sidebar-toggle" onclick={() => isSidebarOpen = !isSidebarOpen} title="Toggle Sidebar">
			{isSidebarOpen ? '◀' : '▶'}
		</button>

		<section class="explore-page container">
			<div class="chat-history">
				{#if !currentSessionId && sessions.length === 0}
					<div class="empty-state">
						<p>Start a new conversation to begin research.</p>
					</div>
				{/if}

				{#each chatHistory as msg, i}
					<div class="message message--{msg.role}">
						{#if msg.role === 'user'}
							<div class="user-bubble">
								{msg.content}
							</div>
						{:else}
							<article class="klippy-card">
								<header class="card-meta">
									<div class="meta-left">
										<span class="tag">Klippy</span>
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
											<button class="icon-btn" onclick={() => sendFeedback(true, currentSessionId)} title="Helpful">
                                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 10v12"></path><path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2h0a3.13 3.13 0 0 1 3 3.88Z"></path></svg>
                                            </button>
											<button class="icon-btn" onclick={() => sendFeedback(false, currentSessionId)} title="Not helpful">
                                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 14V2"></path><path d="M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22h0a3.13 3.13 0 0 1-3-3.88Z"></path></svg>
                                            </button>
											<div class="sep"></div>
											<button class="icon-btn" onclick={() => handleSend(chatHistory[i-1]?.content, true)} title="Refresh">
                                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"></path><path d="M21 3v5h-5"></path><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"></path><path d="M3 21v-5h5"></path></svg>
                                            </button>
										</div>
										{#if msg.total_time_ms}
											<span class="timing">{msg.total_time_ms}ms</span>
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
											<span class="toggle-icon" class:rotated={expandedSources.has(i)}>▼</span>
										</button>
										{#if expandedSources.has(i)}
											<div class="sources-grid">
												{#each msg.sources as src}
													<a href={src.url} target="_blank" rel="noopener" class="source-link">
														<span>{src.source === 'github' ? '🐙' : '📎'}</span>
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

				{#if isLoading}
					<div class="loader">
						<div class="loader-bar"></div>
						<p>{loaderVerb}...</p>
					</div>
				{/if}
			</div>
		</section>

		<section class="query-area">
			<div class="container query-container">
				<form class="query-box" onsubmit={(e) => { e.preventDefault(); handleSend(); }}>
					<label for="chat-input" class="sr-only">Message Klippy</label>
					<input
						id="chat-input"
						type="text"
						bind:value={query}
						placeholder="Follow up or ask something new..."
						autocomplete="off"
					/>
					<button type="submit" disabled={isLoading}>
						<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
						<span>Send</span>
					</button>
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
		transition: transform 0.3s ease, margin-left 0.3s ease;
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
		border-radius: 6px;
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
		gap: 10px;
		padding: 10px 12px;
		background: none;
		border: none;
		border-radius: 6px;
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

	.session-actions button:hover { opacity: 1; }

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
		padding: var(--size-12) 0 var(--size-64);
		max-width: 900px;
		margin-inline: auto;
	}

	.chat-history {
		display: flex;
		flex-direction: column;
		gap: var(--size-12);
	}

	.message { display: flex; flex-direction: column; width: 100%; }
	.message--user { align-items: flex-end; }
	.user-bubble {
		background: var(--ink-1);
		color: white;
		padding: var(--size-4) var(--size-6);
		border-radius: 16px 16px 2px 16px;
		max-width: 80%;
		font-size: 1.1rem;
		font-weight: 300;
		box-shadow: var(--shadow-2);
	}

	.klippy-card {
		background: var(--surface);
		border: 1px solid var(--border);
		border-left: 4px solid var(--kings-red);
		box-shadow: 0 4px 24px rgba(0,0,0,0.03);
	}

	.card-meta {
		display: flex; align-items: center; justify-content: space-between;
		padding: var(--size-4) var(--size-6); border-bottom: 1px solid var(--border);
		background: var(--canvas);
	}

	.meta-left, .meta-right { display: flex; align-items: center; gap: var(--size-4); }
	.tag { font-family: var(--font-mono); font-size: 0.65rem; font-weight: 600; text-transform: uppercase; color: var(--kings-red); letter-spacing: 0.12em; }
	
	.badge { font-family: var(--font-mono); font-size: 0.6rem; padding: 2px var(--size-2); border: 1px solid; border-radius: 2px; text-transform: uppercase; }
	.badge--cached { color: var(--teal); border-color: var(--teal); background: var(--teal-light); }
	.badge--context { color: var(--ink-2); border-color: var(--border-dark); }

	.actions { display: flex; gap: var(--size-2); }
	.icon-btn {
		background: none; border: 1px solid var(--border); border-radius: 4px;
		cursor: pointer; padding: 4px; display: flex; align-items: center; justify-content: center; color: var(--ink-2); opacity: 0.5; transition: all 0.15s;
        text-shadow: none;
	}
	.icon-btn:hover { opacity: 1; background: var(--kings-red-light); border-color: var(--kings-red); color: var(--kings-red); }

	.card-content { padding: var(--size-8) var(--size-6); font-family: var(--font-display); font-size: 1.25rem; line-height: 1.8; }

	.card-footer { border-top: 1px solid var(--border); background: var(--canvas); }
	.toggle-btn { width: 100%; display: flex; justify-content: space-between; padding: var(--size-4) var(--size-6); background: none; border: none; cursor: pointer; transition: background 0.1s; text-shadow: none; }
    .toggle-btn:hover { background: rgba(0,0,0,0.02); }
	.toggle-label { font-family: var(--font-mono); font-size: 0.7rem; text-transform: uppercase; color: var(--ink-2); letter-spacing: 0.08em; }
	.toggle-icon { transition: transform 0.2s; font-size: 0.7rem; color: var(--ink-2); }
	.rotated { transform: rotate(180deg); }
	
	.sources-grid { display: flex; flex-wrap: wrap; gap: var(--size-3); padding: 0 var(--size-6) var(--size-6); }
	.source-link { display: inline-flex; align-items: center; gap: 8px; padding: 5px 12px; background: var(--surface); border: 1px solid var(--border); border-radius: 4px; font-size: 0.8rem; color: var(--ink-1); transition: all 0.15s; text-shadow: none; }
	.source-link:hover { border-color: var(--kings-red); color: var(--kings-red); transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.05); }

	.query-area {
		position: sticky; bottom: 0; background: linear-gradient(transparent, var(--canvas) 40%);
		padding: var(--size-12) var(--size-6) var(--size-10); z-index: 100;
	}

	.query-box {
		display: flex; gap: var(--size-5); padding: var(--size-6) var(--size-8);
		background: var(--surface); border: 1px solid var(--border);
		border-top: 4px solid var(--kings-red); box-shadow: 0 -12px 64px rgba(0,0,0,0.08);
	}

	#chat-input { flex: 1; border: none; outline: none; font-size: 1.15rem; font-weight: 300; background: transparent; }
	button[type='submit'] { background: var(--kings-red); color: white; border: none; padding: 12px 24px; border-radius: 4px; font-weight: 600; cursor: pointer; transition: background 0.15s; font-size: 0.95rem; text-shadow: none; }
    button[type='submit']:hover { background: #b00018; }

	.loader { margin-top: 3rem; text-align: center; }
	.loader-bar { height: 2px; background: var(--border); position: relative; overflow: hidden; }
	.loader-bar::after { content: ''; position: absolute; top: 0; left: -35%; width: 35%; height: 100%; background: var(--kings-red); animation: scan 1.3s linear infinite; }
	@keyframes scan { 0% { left: -35%; } 100% { left: 100%; } }
	.loader p { font-family: var(--font-mono); font-size: 0.8rem; margin-top: 1rem; color: var(--ink-2); letter-spacing: 0.05em; }

	.empty-state { text-align: center; padding: 10vh 0; color: var(--ink-2); font-family: var(--font-display); font-size: 1.5rem; font-style: italic; opacity: 0.5; }

	@media (max-width: 768px) {
		.sidebar { position: fixed; height: 100%; z-index: 200; }
		.sidebar.closed { transform: translateX(-100%); }
	}
</style>
