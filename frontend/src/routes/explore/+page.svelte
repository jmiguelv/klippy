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
	}

	// State (Svelte 5 Runes)
	let chatHistory = $state<Message[]>([]);
	let query = $state('');
	let isLoading = $state(false);
	let loaderVerb = $state('Synthesising');
	let sessionId = $state('');
	let expandedSources = $state<Set<number>>(new Set()); // Track expanded state for each message

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

	async function sendFeedback(isPositive: boolean, index: number) {
		try {
			await fetch('http://localhost:8000/feedback', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ session_id: getSessionId(), is_positive: isPositive })
			});
			if (!isPositive) {
				alert('Session history cleared on server. Starting fresh!');
				chatHistory = [];
			}
		} catch (e) {
			console.error(e);
		}
	}

	async function handleSend(textOverride?: string, isRefresh = false) {
		const text = textOverride || query.trim();
		if (!text) return;

		if (!textOverride) query = '';
		if (!isRefresh) {
			chatHistory = [...chatHistory, { role: 'user', content: text }];
		}

		isLoading = true;
		let verbIndex = 0;
		const interval = setInterval(() => {
			loaderVerb = LOADER_VERBS[++verbIndex % LOADER_VERBS.length];
		}, 2000);

		if (isRefresh) {
			await fetch('http://localhost:8000/feedback', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ session_id: getSessionId(), is_positive: false })
			});
		}

		try {
			const response = await fetch('http://localhost:8000/query', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ text, session_id: getSessionId() })
			});
			const data = await response.json();

			const newMessage: Message = {
				role: 'klippy',
				content: data.answer,
				sources: data.sources,
				total_time_ms: data.total_time_ms,
				cached_at: data.cached_at,
				is_cached: data.cached
			};

			if (isRefresh) {
				chatHistory[chatHistory.length - 1] = newMessage;
			} else {
				chatHistory = [...chatHistory, newMessage];
			}
		} catch (e) {
			console.error(e);
			chatHistory = [
				...chatHistory,
				{ role: 'klippy', content: 'Error: Could not connect to the research engine.' }
			];
		} finally {
			clearInterval(interval);
			isLoading = false;
			// Scroll to bottom
			setTimeout(() => window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' }), 50);
		}
	}

	// Svelte 5 Effect for URL parameters
	$effect(() => {
		const q = page.url.searchParams.get('q');
		if (q && chatHistory.length === 0 && !isLoading) {
			handleSend(q);
		}
	});

	onMount(() => {
		getSessionId();
	});
</script>

<svelte:head>
	<title>Explore — Klippy Chat</title>
</svelte:head>

<section class="explore-page container">
	<div class="chat-history">
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
									<span class="badge badge--cached" title={msg.cached_at}>⚡ Cached</span>
								{/if}
							</div>
							<div class="meta-right">
								<div class="actions">
									<button class="icon-btn" onclick={() => sendFeedback(true, i)} title="Helpful"
										>👍</button
									>
									<button class="icon-btn" onclick={() => sendFeedback(false, i)} title="Not helpful"
										>👎</button
									>
									<div class="sep"></div>
									<button class="icon-btn" onclick={() => handleSend(msg.content, true)} title="Refresh"
										>🔄</button
									>
								</div>
								{#if msg.total_time_ms}
									<span class="timing">{msg.total_time_ms}ms</span>
								{/if}
							</div>
						</header>

						<div class="card-content markdown-body">
							<!-- Using @html strictly for trusted markdown output -->
							{@html marked.parse(msg.content)}
						</div>

						{#if msg.sources && msg.sources.length > 0}
							<footer class="card-footer">
								<button class="toggle-btn" onclick={() => toggleSources(i)}>
									<span>Referenced Sources</span>
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
				<svg
					width="18"
					height="18"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					stroke-linecap="round"
					stroke-linejoin="round"
				>
					<line x1="22" y1="2" x2="11" y2="13"></line>
					<polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
				</svg>
				<span>Send</span>
			</button>
		</form>
	</div>
</section>

<style>
	.explore-page {
		padding: var(--size-10) 0 var(--size-48);
		min-height: 60vh;
	}

	.chat-history {
		display: flex;
		flex-direction: column;
		gap: var(--size-10);
		max-width: 800px;
		margin-inline: auto;
	}

	.message {
		display: flex;
		flex-direction: column;
		width: 100%;
	}

	.message--user {
		align-items: flex-end;
	}

	.user-bubble {
		background: var(--ink-1);
		color: white;
		padding: var(--size-3) var(--size-5);
		border-radius: 16px 16px 2px 16px;
		max-width: 80%;
		font-weight: 300;
		box-shadow: var(--shadow-2);
	}

	.klippy-card {
		background: var(--surface);
		border: 1px solid var(--border);
		border-left: 4px solid var(--kings-red);
		box-shadow: var(--shadow-1);
	}

	.card-meta {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: var(--size-3) var(--size-5);
		border-bottom: 1px solid var(--border);
		background: var(--canvas);
	}

	.meta-left,
	.meta-right {
		display: flex;
		align-items: center;
		gap: var(--size-3);
	}

	.tag {
		font-family: var(--font-mono);
		font-size: 0.6rem;
		font-weight: 600;
		text-transform: uppercase;
		color: var(--kings-red);
		letter-spacing: 0.1em;
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

	.actions {
		display: flex;
		gap: var(--size-1);
	}

	.icon-btn {
		background: none;
		border: none;
		cursor: pointer;
		padding: 2px;
		font-size: 0.8rem;
		opacity: 0.5;
		transition: opacity 0.15s;
	}

	.icon-btn:hover {
		opacity: 1;
	}

	.sep {
		width: 1px;
		height: 12px;
		background: var(--border-dark);
		margin-inline: 2px;
	}

	.timing {
		font-family: var(--font-mono);
		font-size: 0.65rem;
		color: var(--ink-2);
	}

	.card-content {
		padding: var(--size-6) var(--size-5);
		font-family: var(--font-display);
		font-size: 1.15rem;
	}

	.card-footer {
		border-top: 1px solid var(--border);
		background: var(--canvas);
	}

	.toggle-btn {
		width: 100%;
		display: flex;
		justify-content: space-between;
		padding: var(--size-3) var(--size-5);
		background: none;
		border: none;
		cursor: pointer;
		font-family: var(--font-mono);
		font-size: 0.65rem;
		text-transform: uppercase;
		color: var(--ink-2);
	}

	.toggle-icon {
		transition: transform 0.2s;
	}

	.rotated {
		transform: rotate(180deg);
	}

	.sources-grid {
		display: flex;
		flex-wrap: wrap;
		gap: var(--size-2);
		padding: 0 var(--size-5) var(--size-4);
	}

	.source-link {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		padding: 4px 8px;
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: 4px;
		font-size: 0.75rem;
		color: var(--ink-1);
	}

	.source-link:hover {
		border-color: var(--kings-red);
		color: var(--kings-red);
	}

	/* ── Loader ───────────────────────────────────── */
	.loader {
		max-width: 800px;
		margin-inline: auto;
	}

	.loader-bar {
		height: 2px;
		background: var(--border);
		position: relative;
		overflow: hidden;
	}

	.loader-bar::after {
		content: '';
		position: absolute;
		top: 0;
		left: -35%;
		width: 35%;
		height: 100%;
		background: var(--kings-red);
		animation: scan 1.3s linear infinite;
	}

	@keyframes scan {
		0% {
			left: -35%;
		}
		100% {
			left: 100%;
		}
	}

	.loader p {
		font-family: var(--font-mono);
		font-size: 0.75rem;
		text-align: center;
		margin-top: 0.5rem;
		color: var(--ink-2);
	}

	/* ── Query Box ────────────────────────────────── */
	.query-area {
		position: fixed;
		bottom: 0;
		left: 0;
		right: 0;
		background: linear-gradient(transparent, var(--canvas) 30%);
		padding: var(--size-10) var(--size-6) var(--size-8);
		z-index: 100;
	}

	.query-container {
		max-width: 800px;
	}

	.query-box {
		display: flex;
		gap: var(--size-4);
		padding: var(--size-4) var(--size-6);
		background: var(--surface);
		border: 1px solid var(--border);
		border-top: 4px solid var(--kings-red);
		box-shadow: var(--shadow-4);
	}

	#chat-input {
		flex: 1;
		border: none;
		outline: none;
		font-size: 1.1rem;
		font-weight: 300;
		background: transparent;
	}

	button[type='submit'] {
		display: inline-flex;
		align-items: center;
		gap: 8px;
		background: var(--kings-red);
		color: white;
		border: none;
		padding: 8px 16px;
		border-radius: 4px;
		font-weight: 600;
		cursor: pointer;
	}

	button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.sr-only {
		position: absolute;
		width: 1px;
		height: 1px;
		padding: 0;
		margin: -1px;
		overflow: hidden;
		clip: rect(0, 0, 0, 0);
		white-space: nowrap;
		border-width: 0;
	}

	@media (max-width: 640px) {
		.query-area {
			padding: var(--size-4);
		}
		button span {
			display: none;
		}
	}
</style>
