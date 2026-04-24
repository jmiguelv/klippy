<script lang="ts">
	import '../app.css';
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import { Sun, Moon } from 'lucide-svelte';

	let { children } = $props();

	let isExplore = $derived(page.url.pathname.startsWith('/chats'));
	let theme = $state<'light' | 'dark'>('light');

	function toggleTheme() {
		theme = theme === 'light' ? 'dark' : 'light';
		document.documentElement.dataset.theme = theme;
		localStorage.setItem('klippy_theme', theme);
	}

	onMount(() => {
		const savedTheme = localStorage.getItem('klippy_theme') as 'light' | 'dark' | null;
		if (savedTheme) {
			theme = savedTheme;
			document.documentElement.dataset.theme = theme;
		}
	});

	$effect(() => {
		document.body.style.overflow = isExplore ? 'hidden' : '';
	});
</script>

<svelte:head>
	<title>Klippy</title>
</svelte:head>

<div class="page-rule" aria-hidden="true"></div>

<nav class="main-nav">
	<div class="container nav-inner">
		<a href="/" class="nav-wordmark">Klippy</a>
		<div class="nav-links">
			<a href="/chats/" class="nav-link">Chats</a>
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

{#if !isExplore}
	<footer class="site-footer">
		<div class="container footer-inner">
			<span class="footer-brand">King's Digital Lab</span>
			<span class="footer-stack">LlamaIndex · Qdrant · Redis · Arize Phoenix</span>
		</div>
	</footer>
{/if}

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
	}

	.nav-links {
		display: flex;
		align-items: center;
		gap: var(--size-6);
	}

	.nav-link {
		font-family: var(--font-sans);
		font-size: 0.95rem;
		font-weight: 500;
		color: var(--ink-0);
		transition: color 0.15s;
		text-decoration: underline;
		text-underline-offset: 4px;
		text-decoration-color: transparent;
	}

	.nav-link:hover {
		color: var(--kings-red);
		text-decoration-color: var(--kings-red);
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
		transition: background 0.15s, color 0.15s;
	}

	.nav-theme-toggle:hover {
		background: var(--canvas);
		color: var(--kings-red);
	}

	.site-footer {
		border-top: 1px solid var(--border);
		background: var(--canvas);
		padding: var(--size-10) 0;
		margin-top: auto;
	}

	.footer-inner {
		display: flex;
		align-items: center;
		justify-content: space-between;
	}

	.footer-brand {
		font-family: var(--font-display);
		font-size: 0.9rem;
		color: var(--ink-2);
		font-style: italic;
		font-weight: 300;
	}

	.footer-stack {
		font-family: var(--font-mono);
		font-size: 0.65rem;
		color: var(--ink-2);
		letter-spacing: 0.1em;
		text-transform: uppercase;
		font-weight: 300;
		opacity: 0.6;
	}

	@media (max-width: 640px) {
		.footer-inner {
			flex-direction: column;
			gap: var(--size-4);
			text-align: center;
		}
	}
</style>
