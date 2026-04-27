<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { Sun, Moon } from 'lucide-svelte';

	let { children } = $props();

	let theme = $state<'light' | 'dark'>('light');
	let userName = $state('');

	function toggleTheme() {
		theme = theme === 'light' ? 'dark' : 'light';
		document.documentElement.dataset.theme = theme;
		localStorage.setItem('klippy_theme', theme);
	}

	function switchUser() {
		localStorage.removeItem('klippy_user_name');
		goto('/');
	}

	onMount(() => {
		const savedTheme = localStorage.getItem('klippy_theme') as 'light' | 'dark' | null;
		if (savedTheme) {
			theme = savedTheme;
			document.documentElement.dataset.theme = theme;
		}
		userName = localStorage.getItem('klippy_user_name') ?? '';
		document.body.style.overflow = 'hidden';
	});
</script>

<svelte:head>
	<title>Klippy</title>
</svelte:head>

<div class="page-rule" aria-hidden="true"></div>

<nav class="main-nav">
	<div class="container nav-inner">
		<a href="/chats/" class="nav-wordmark">Klippy <span class="nav-org">King's Digital Lab</span></a
		>
		<div class="nav-links">
			{#if userName}
				<button class="nav-user" onclick={switchUser} title="Switch user">{userName}</button>
			{/if}
			<button class="nav-theme-toggle" onclick={toggleTheme} title="Toggle Dark/Light Mode">
				{#if theme === 'light'}
					<Moon size={16} />
				{:else}
					<Sun size={16} />
				{/if}
			</button>
		</div>
	</div>
</nav>

{@render children()}

<style>
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

	.nav-user:hover {
		color: var(--kings-red);
	}

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
		transition:
			background 0.15s,
			color 0.15s;
	}

	.nav-theme-toggle:hover {
		background: var(--canvas);
		color: var(--kings-red);
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

		.nav-org::before {
			display: none;
		}
	}
</style>
