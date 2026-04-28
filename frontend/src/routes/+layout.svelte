<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { Sun, Moon, Plus, MessageSquare, Pencil, Trash2, ChevronLeft, ChevronRight, Map } from 'lucide-svelte';
	import { chatState } from '$lib/chat-state.svelte';

	let { children } = $props();

	let theme = $state<'light' | 'dark'>(
		typeof localStorage !== 'undefined' ? (localStorage.getItem('klippy_theme') as 'light' | 'dark') || 'light' : 'light'
	);
	let userName = $state('');
	let isSidebarOpen = $state(
		typeof localStorage !== 'undefined' ? localStorage.getItem('klippy_sidebar_open') === 'true' : false
	);

	let currentId = $derived(page.params.id ?? '');
	let showSidebar = $derived(page.url.pathname !== '/');

	$effect(() => {
		localStorage.setItem('klippy_sidebar_open', String(isSidebarOpen));
	});

	onMount(() => {
		userName = localStorage.getItem('klippy_user_name') ?? '';
		document.body.style.overflow = 'hidden';
		chatState.loadSessions();
	});

	function toggleTheme() {
		theme = theme === 'light' ? 'dark' : 'light';
		document.documentElement.dataset.theme = theme;
		localStorage.setItem('klippy_theme', theme);
	}

	function switchUser() {
		localStorage.removeItem('klippy_user_name');
		goto('/');
	}

	function newChat() {
		const id = chatState.createNewChat();
		goto('/chats/' + id + '/');
	}

	function selectChat(id: string) {
		goto('/chats/' + id + '/');
	}

	function deleteChat(id: string, e: Event) {
		e.stopPropagation();
		if (!confirm('Are you sure you want to delete this chat?')) return;
		const nextId = chatState.deleteChat(id);
		if (id === currentId) {
			goto(nextId ? '/chats/' + nextId + '/' : '/chats/');
		}
	}

	function renameChat(id: string, e: Event) {
		e.stopPropagation();
		const session = chatState.sessions.find((s) => s.id === id);
		if (!session) return;
		const newTitle = prompt('Rename chat:', session.title);
		if (newTitle?.trim()) {
			chatState.renameChat(id, newTitle.trim());
		}
	}
</script>

<svelte:head>
	<title>Klippy</title>
</svelte:head>

<div class="page-rule" aria-hidden="true"></div>

<nav class="main-nav">
	<div class="container nav-inner">
		<a href="/chats/" class="nav-wordmark">Klippy <span class="nav-org">King's Digital Lab</span></a>
		<div class="nav-links">
			{#if userName}
				<button class="nav-user" onclick={switchUser} title="Switch user">{userName}</button>
			{/if}
			<button class="nav-theme-toggle" onclick={toggleTheme} title="Toggle Dark/Light Mode">
				{#if theme === 'light'}<Moon size={16} />{:else}<Sun size={16} />{/if}
			</button>
		</div>
	</div>
</nav>

{#if showSidebar}
	<div class="app-layout">
		{#if isSidebarOpen}
			<div class="sidebar-backdrop" aria-hidden="true" onclick={() => (isSidebarOpen = false)}></div>
		{/if}

		<aside class="sidebar" class:closed={!isSidebarOpen}>
			<header class="sidebar-header">
				<div class="header-top">
					{#if isSidebarOpen}
						<div class="wordmark-wrap">
							<span class="sidebar-wordmark">Chats</span>
						</div>
					{/if}
					<button
						class="sidebar-toggle-inside"
						onclick={() => (isSidebarOpen = !isSidebarOpen)}
						title="Toggle Sidebar"
						aria-label={isSidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
					>
						{#if isSidebarOpen}<ChevronLeft size={16} />{:else}<ChevronRight size={16} />{/if}
					</button>
				</div>

				<button
					class="new-chat-btn"
					class:compact={!isSidebarOpen}
					onclick={newChat}
					title={isSidebarOpen ? undefined : 'New Chat'}
				>
					<Plus size={16} />
					{#if isSidebarOpen}<span>New Chat</span>{/if}
				</button>
			</header>

			<div class="session-list">
				{#each chatState.sessions as s}
					<div
						role="button"
						tabindex="0"
						class="session-item"
						class:active={currentId === s.id}
						title={isSidebarOpen ? undefined : s.title}
						onclick={() => selectChat(s.id)}
						onkeydown={(e) => e.key === 'Enter' && selectChat(s.id)}
					>
						<MessageSquare class="session-icon" size={14} />
						{#if isSidebarOpen}
							<span class="session-title">{s.title}</span>
							<div class="session-actions">
								<button onclick={(e) => renameChat(s.id, e)} title="Rename"><Pencil size={12} /></button>
								<button onclick={(e) => deleteChat(s.id, e)} title="Delete"><Trash2 size={12} /></button>
							</div>
						{/if}
					</div>
				{/each}
			</div>

			<nav class="sidebar-nav">
				<a
					href="/explore"
					class="sidebar-nav-link"
					class:active={page.url.pathname.startsWith('/explore')}
					title={isSidebarOpen ? undefined : 'Explore'}
				>
					<Map size={14} />
					{#if isSidebarOpen}<span>Explore</span>{/if}
				</a>
			</nav>
		</aside>

		<div class="app-content">
			<button
				class="sidebar-toggle-mobile"
				onclick={() => (isSidebarOpen = true)}
				aria-label="Open sidebar"
			>
				<ChevronRight size={14} />
			</button>
			{@render children()}
		</div>
	</div>
{:else}
	{@render children()}
{/if}

<style>
	/* ── Nav ────────────────────────────────────── */
	.main-nav {
		border-bottom: 1px solid var(--border);
		background: var(--canvas);
		position: sticky;
		top: 0;
		z-index: 100;
	}

	.nav-inner {
		height: 56px;
		display: flex;
		align-items: center;
		justify-content: space-between;
	}

	.nav-wordmark {
		font-family: var(--font-display);
		font-size: 1.4rem;
		font-weight: 600;
		color: var(--ink-0);
		letter-spacing: 0.02em;
		display: flex;
		align-items: baseline;
		gap: var(--size-3);
	}

	.nav-org {
		font-family: var(--font-mono);
		font-size: 0.62rem;
		font-weight: 400;
		text-transform: uppercase;
		letter-spacing: 0.12em;
		color: var(--ink-3);
	}

	.nav-org::before {
		content: '|';
		margin-right: var(--size-3);
		opacity: 0.4;
	}

	.nav-links {
		display: flex;
		align-items: center;
		gap: var(--size-6);
	}

	.nav-user {
		background: none;
		border: none;
		cursor: pointer;
		font-family: var(--font-mono);
		font-size: 0.68rem;
		text-transform: uppercase;
		letter-spacing: 0.1em;
		color: var(--ink-2);
		padding: var(--size-1) var(--size-2);
		border-radius: 3px;
		transition: color 0.15s;
	}

	.nav-user:hover { color: var(--kings-red); }

	.nav-theme-toggle {
		background: none;
		border: none;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: var(--size-2);
		color: var(--ink-2);
		border-radius: 4px;
		transition: background 0.15s, color 0.15s;
	}

	.nav-theme-toggle:hover {
		background: var(--canvas);
		color: var(--kings-red);
	}

	/* ── App layout (sidebar + content) ─────────── */
	.app-layout {
		display: flex;
		height: calc(100vh - 57px);
		overflow: hidden;
		background: var(--canvas);
	}

	.app-content {
		flex: 1;
		display: flex;
		flex-direction: column;
		overflow: hidden;
		position: relative;
	}

	/* ── Sidebar ────────────────────────────────── */
	.sidebar {
		width: 280px;
		background: var(--surface);
		border-right: 1px solid var(--border);
		display: flex;
		flex-direction: column;
		transition: width 0.25s ease;
		overflow: hidden;
	}

	.sidebar.closed { width: 56px; }

	.sidebar-header {
		padding: var(--size-4);
		display: flex;
		flex-direction: column;
		gap: var(--size-4);
		border-bottom: 1px solid var(--border);
	}

	.header-top {
		display: flex;
		align-items: center;
		justify-content: space-between;
		min-height: 32px;
	}

	.wordmark-wrap { padding: 0 var(--size-2); }

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

	.new-chat-btn:hover { background: var(--kings-red-light); }

	.new-chat-btn.compact {
		padding: var(--size-2);
		width: 32px;
		height: 32px;
		align-self: center;
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

	.session-item:hover { background: var(--canvas); }

	.session-item.active {
		border-left: 2px solid var(--kings-red);
		color: var(--kings-red);
		border-radius: 0 4px 4px 0;
	}

	:global(.session-icon) {
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

	.session-actions { display: none; gap: 4px; }
	.session-item:hover .session-actions { display: flex; }

	.session-actions button {
		background: none;
		border: none;
		cursor: pointer;
		font-size: 0.8rem;
		padding: 2px;
		color: var(--ink-2);
		opacity: 0.6;
	}

	.session-actions button:hover { color: var(--ink-0); opacity: 1; }

	@media (hover: none) {
		.session-actions { display: flex; opacity: 0.4; }
	}

	.sidebar-toggle-inside {
		background: none;
		border: none;
		cursor: pointer;
		padding: var(--size-1);
		color: var(--ink-2);
		border-radius: 4px;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: color 0.15s;
	}

	.sidebar-toggle-inside:hover { color: var(--ink-0); }

	.sidebar.closed .sidebar-header {
		align-items: center;
		padding: var(--size-3) var(--size-2);
	}

	.sidebar.closed .header-top { justify-content: center; }

	.sidebar.closed .session-item {
		justify-content: center;
		padding: var(--size-2);
	}

	.sidebar.closed :global(.session-icon) { opacity: 0.6; }

	.sidebar-nav {
		border-top: 1px solid var(--border);
		padding: var(--size-2);
	}

	.sidebar-nav-link {
		display: flex;
		align-items: center;
		gap: var(--size-2);
		padding: var(--size-2) var(--size-3);
		border-radius: 4px;
		color: var(--ink-2);
		text-decoration: none;
		font-family: var(--font-sans);
		font-size: 0.85rem;
		transition: background 0.15s, color 0.15s;
	}

	.sidebar-nav-link:hover { background: var(--canvas); color: var(--ink-0); }
	.sidebar-nav-link.active { color: var(--kings-red); }

	.sidebar.closed .sidebar-nav { padding: var(--size-2); }
	.sidebar.closed .sidebar-nav-link { justify-content: center; padding: var(--size-2); }

	.sidebar-toggle-mobile { display: none; }
	.sidebar-backdrop { display: none; }

	/* ── Responsive ──────────────────────────────── */
	@media (max-width: 768px) {
		.app-content { padding-top: 60px; }

		.sidebar-toggle-mobile {
			display: flex;
			position: absolute;
			top: 20px;
			left: 20px;
			z-index: 110;
			background: var(--surface);
			border: 1px solid var(--border);
			border-radius: 4px;
			width: 32px;
			height: 32px;
			align-items: center;
			justify-content: center;
			color: var(--ink-2);
			box-shadow: var(--shadow-2);
		}

		.sidebar {
			position: fixed;
			width: 280px;
			height: 100%;
			z-index: 200;
		}

		.sidebar.closed {
			width: 280px;
			transform: translateX(-100%);
		}

		.sidebar-backdrop {
			display: block;
			position: fixed;
			inset: 0;
			background: rgba(0, 0, 0, 0.4);
			z-index: 199;
		}
	}

	@media (max-width: 640px) {
		.nav-inner {
			height: auto;
			padding-top: var(--size-3);
			padding-bottom: var(--size-3);
		}

		.nav-wordmark {
			flex-direction: column;
			gap: 2px;
			align-items: flex-start;
		}

		.nav-org::before { display: none; }
		.sidebar-header { padding: var(--size-3); }
	}
</style>
