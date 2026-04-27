<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { chatState } from '$lib/chat-state.svelte';
	import { Plus, MessageSquare, Pencil, Trash2, ChevronLeft, ChevronRight } from 'lucide-svelte';

	let { children } = $props();

	let isSidebarOpen = $state(false);
	let currentId = $derived(page.params.id ?? '');

	onMount(() => {
		chatState.loadSessions();
	});

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

<div class="chat-layout">
	{#if isSidebarOpen}
		<div class="sidebar-backdrop" aria-hidden="true" onclick={() => (isSidebarOpen = false)}></div>
	{/if}

	<aside class="sidebar" class:closed={!isSidebarOpen}>
		<header class="sidebar-header">
			<div class="wordmark-wrap">
				<span class="sidebar-wordmark">Chats</span>
			</div>
			<button class="new-chat-btn" onclick={newChat}>
				<Plus size={16} />
				<span>New Chat</span>
			</button>
			<button
				class="sidebar-close"
				onclick={() => (isSidebarOpen = false)}
				aria-label="Close sidebar"
			>
				<ChevronLeft size={16} />
			</button>
		</header>

		<div class="session-list">
			{#each chatState.sessions as s}
				<div
					role="button"
					tabindex="0"
					class="session-item"
					class:active={currentId === s.id}
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

	<div class="chat-content">
		<button
			class="sidebar-toggle"
			onclick={() => (isSidebarOpen = !isSidebarOpen)}
			title="Toggle Sidebar"
		>
			{#if isSidebarOpen}<ChevronLeft size={14} />{:else}<ChevronRight size={14} />{/if}
		</button>

		{@render children()}
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
		color: var(--ink-2);
		opacity: 0.6;
	}

	.session-actions button:hover {
		color: var(--ink-0);
		opacity: 1;
	}

	@media (hover: none) {
		.session-actions {
			display: flex;
			opacity: 0.4;
		}
	}

	/* ── Content area ──────────────────────────── */
	.chat-content {
		flex: 1;
		display: flex;
		flex-direction: column;
		overflow: hidden;
		position: relative;
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

	.sidebar-backdrop {
		display: none;
	}

	.sidebar-close {
		display: none;
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

		.sidebar-backdrop {
			display: block;
			position: fixed;
			inset: 0;
			background: rgba(0, 0, 0, 0.4);
			z-index: 199;
		}

		.sidebar-close {
			display: flex;
			align-items: center;
			justify-content: center;
			background: none;
			border: none;
			cursor: pointer;
			color: var(--ink-2);
			padding: var(--size-2);
			margin-left: auto;
		}

		.sidebar-close:hover {
			color: var(--ink-0);
		}
	}

	@media (max-width: 640px) {
		.sidebar-header {
			padding: var(--size-3);
		}
	}
</style>
