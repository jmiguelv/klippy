<script lang="ts">
	import '../app.css';
	let { children } = $props();
</script>

<svelte:head>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
    <link
        href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=IBM+Plex+Mono:wght@300;400;500&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap"
        rel="stylesheet"
    />
</svelte:head>

<div class="page-rule" aria-hidden="true"></div>

<nav class="main-nav">
	<div class="container nav-inner">
		<a href="/" class="nav-wordmark">Klippy</a>
        <div class="nav-links">
            <a href="/explore/" class="nav-link">Explore</a>
        </div>
	</div>
</nav>

{@render children()}

<footer class="site-footer">
	<div class="container footer-inner">
		<span class="footer-brand">King's Digital Lab</span>
		<span class="footer-stack">LlamaIndex · Qdrant · Redis · Arize Phoenix</span>
	</div>
</footer>

<style>
	.main-nav {
		border-bottom: 1px solid var(--border);
		background: var(--surface);
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
