<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { chatState } from '$lib/chat-state.svelte';
	import IdentityForm from '$lib/IdentityForm.svelte';
	import ChatHero from '$lib/ChatHero.svelte';

	onMount(() => {
		const q = new URLSearchParams(window.location.search).get('q');
		if (q && chatState.userName) {
			history.replaceState({}, '', window.location.pathname);
			const { text, filters } = parseFilters(q);
			const id = chatState.createNewChat(text, filters);
			goto(`/chats/${id}/`); 
		}
		
		document.body.style.overflow = '';
	});

	function parseFilters(raw: string): { text: string; filters: Record<string, string> } {
		const filters: Record<string, string> = {};
		const text = raw
			.replace(/@(\w+):(?:"([^"]+)"|(\S+))/g, (_, k, quoted, unquoted) => {
				filters[k] = quoted ?? unquoted;
				return '';
			})
			.trim();
		return { text, filters };
	}
</script>

<svelte:head>
	<title>{chatState.userName ? 'Chats' : 'Klippy'} — King's Digital Lab</title>
</svelte:head>

{#if !chatState.userName}
	<main class="identity-page">
		<div class="container">
			<IdentityForm />
		</div>
	</main>
{:else}
	<ChatHero />
{/if}

<style>
	.identity-page {
		height: calc(100vh - 57px);
		overflow: hidden;
		display: flex;
		align-items: center;
		background: var(--canvas);
	}
</style>
