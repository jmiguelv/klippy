<script lang="ts">
	import { goto } from '$app/navigation';

	let query = $state('');

	function handleSearch(e: Event) {
		e.preventDefault();
		if (!query.trim()) return;
		goto(`/explore/?q=${encodeURIComponent(query.trim())}`);
	}
</script>

<svelte:head>
	<title>Klippy — King's Digital Lab</title>
</svelte:head>

<main class="landing-page">
    <section class="landing-hero">
        <div class="container hero-inner">
            <header class="hero-text">
                <p class="hero-eyebrow">King's Digital Lab</p>
                <h1 class="hero-heading">Ask anything about<br/>your research projects.</h1>
                <p class="hero-description">
                    Search across ClickUp tasks, GitHub repositories,<br class="break" /> and internal documentation.
                </p>
            </header>

            <form class="search-form" onsubmit={handleSearch}>
                <div class="query-box">
                    <label for="landing-search" class="query-label">Query</label>
                    <div class="query-input-row">
                        <input
                            id="landing-search"
                            type="text"
                            bind:value={query}
                            placeholder="What needs doing on the Slavery in War project?"
                            autocomplete="off"
                        />
                        <button type="submit" aria-label="Explore">
                            <svg
                                width="16"
                                height="16"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                stroke-width="2"
                                stroke-linecap="round"
                                stroke-linejoin="round"
                            >
                                <line x1="5" y1="12" x2="19" y2="12"></line>
                                <polyline points="12 5 19 12 12 19"></polyline>
                            </svg>
                            <span>Explore</span>
                        </button>
                    </div>
                    <p class="query-hint">Press <kbd>↵ Enter</kbd> to search</p>
                </div>
            </form>
        </div>
    </section>
</main>

<style>
    .landing-page {
        flex: 1;
        display: flex;
        flex-direction: column;
    }

	.landing-hero {
		flex: 1;
		display: flex;
		align-items: center;
		padding: var(--size-12) 0;
		background: var(--canvas);
	}

	.hero-inner {
		width: 100%;
		max-width: 800px;
		display: flex;
		flex-direction: column;
		gap: var(--size-12);
        padding-bottom: 10vh;
	}

	.hero-eyebrow {
		font-family: var(--font-mono);
		font-size: 0.7rem;
		color: var(--kings-red);
		text-transform: uppercase;
		letter-spacing: 0.12em;
		margin-bottom: var(--size-6);
	}

	.hero-heading {
		font-size: clamp(3rem, 10vw, 4.8rem);
		font-weight: 500;
		line-height: 1.05;
		margin-bottom: var(--size-6);
		color: var(--ink-0);
		letter-spacing: -0.01em;
	}

	.hero-description {
		font-size: 1rem;
		line-height: 1.6;
		color: var(--ink-2);
		max-width: 520px;
		font-weight: 300;
	}

	.search-form {
		width: 100%;
		max-width: 720px;
	}

	.query-box {
        display: flex;
        flex-direction: column;
        gap: var(--size-3);
        padding: var(--size-6) var(--size-7);
        background: var(--surface);
        border: 1px solid var(--border);
        border-top: 4px solid var(--kings-red);
        box-shadow: 0 4px 32px rgba(0, 0, 0, 0.03);
	}

    .query-label {
        font-family: var(--font-mono);
        font-size: 0.65rem;
        font-weight: 600;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        color: var(--kings-red);
    }

    .query-input-row {
        display: flex;
        align-items: center;
        gap: var(--size-4);
        border-bottom: 1px solid var(--border-dark);
        padding-bottom: var(--size-2);
    }

	input {
		flex: 1;
		border: none;
		padding: var(--size-2) 0;
		font-size: 1.1rem;
		font-family: var(--font-sans);
		outline: none;
		background: transparent;
		font-weight: 300;
        color: var(--ink-0);
	}

    input::placeholder {
        color: var(--ink-2);
        opacity: 0.5;
    }

	button {
		display: inline-flex;
		align-items: center;
		gap: var(--size-2);
		background: var(--kings-red);
		color: white;
		border: none;
		padding: 8px 16px;
		font-weight: 500;
		cursor: pointer;
		transition: background 0.15s;
		font-size: 0.85rem;
        border-radius: 2px;
        text-shadow: none;
	}

	button:hover {
		background: #b00018;
	}

	.query-hint {
		margin-top: var(--size-1);
		font-size: 0.8rem;
		color: var(--ink-2);
		font-family: var(--font-sans);
		font-weight: 300;
	}

    kbd {
        font-family: var(--font-mono);
        color: var(--ink-1);
        font-size: 0.8rem;
    }

	@media (max-width: 640px) {
		.query-input-row {
			flex-direction: column;
            align-items: stretch;
		}
		button {
			justify-content: center;
		}
        .hero-inner { padding-bottom: 0; }
        .break { display: none; }
	}
</style>
