# Frontend Inconsistency Fixes & Architectural Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve design and architectural inconsistencies across the Klippy frontend by consolidating routes, componentizing the composer, and refining UI/UX polish.

**Architecture:** Use a component-driven approach to eliminate duplication. Move identity logic into the root route and search settings into global state. Extract autocomplete into a reusable action.

**Tech Stack:** Svelte 5 (Runes), TypeScript, Lucide Svelte, Vanilla CSS.

---

### Task 0: Branch and Prepare

- [ ] **Step 1: Create a new branch**
Run: `git checkout -b refactor/frontend-consolidation`
Expected: Switched to a new branch 'refactor/frontend-consolidation'

- [ ] **Step 2: Define Z-index variables**
Modify: `frontend/src/app.css`
```css
:root {
	/* ... existing tokens ... */
	--z-hide: -1;
	--z-base: 1;
	--z-nav: 100;
	--z-sidebar: 200;
	--z-dropdown: 300;
	--z-modal: 400;
	--z-toast: 500;
}
```

- [ ] **Step 3: Commit**
Run: `git add frontend/src/app.css && git commit -m "chore: define semantic z-index variables"`

---

### Task 1: FOUC Prevention & Dark Mode Polish

- [ ] **Step 1: Move theme detection to app.html**
Modify: `frontend/src/app.html`
```html
<head>
	<meta charset="utf-8" />
	<link rel="icon" href="%sveltekit.assets%/favicon.svg" />
	<meta name="viewport" content="width=device-width, initial-scale=1" />
	<script>
		(function() {
			const theme = localStorage.getItem('klippy_theme') || 'light';
			document.documentElement.dataset.theme = theme;
		})();
	</script>
	%sveltekit.head%
</head>
```

- [ ] **Step 2: Remove redundant theme logic from +layout.svelte**
Modify: `frontend/src/routes/+layout.svelte`
```typescript
	onMount(() => {
		// Remove the theme loading block here, keep the rest
		userName = localStorage.getItem('klippy_user_name') ?? '';
		document.body.style.overflow = 'hidden';
		chatState.loadSessions();
	});
```

- [ ] **Step 3: Commit**
Run: `git add frontend/src/app.html frontend/src/routes/+layout.svelte && git commit -m "fix: prevent theme FOUC with blocking script"`

---

### Task 2: Unified Composer Component (Part 1: Logic Extraction)

- [ ] **Step 1: Create useAutocomplete action**
Create: `frontend/src/lib/use-autocomplete.ts`
```typescript
import { KNOWN_FIELDS } from './filters';

export interface AcState {
	visible: boolean;
	mode: 'field' | 'value';
	field: string;
	partial: string;
	options: string[];
	activeIdx: number;
}

export function createAutocomplete() {
	let ac = $state<AcState>({
		visible: false,
		mode: 'field',
		field: '',
		partial: '',
		options: [],
		activeIdx: 0
	});

	// ... logic extracted from [id]/+page.svelte ...
	return {
		get state() { return ac; },
		handleInput: (val: string, cursor: number) => { /* ... */ },
		// ...
	};
}
```

- [ ] **Step 2: Update chatState for settings persistence**
Modify: `frontend/src/lib/chat-state.svelte.ts`
```typescript
class ChatState {
	// ...
	topK = $state(10);
	threshold = $state(0.3);
	// ...
}
```

- [ ] **Step 3: Commit**
Run: `git add frontend/src/lib/use-autocomplete.ts frontend/src/lib/chat-state.svelte.ts && git commit -m "feat: extract autocomplete logic and unify search settings state"`

---

### Task 3: Unified Composer Component (Part 2: Component)

- [ ] **Step 1: Create Composer.svelte**
Create: `frontend/src/lib/Composer.svelte`
```svelte
<script lang="ts">
	// ... props for onSend, showSettingsToggle, placeholder ...
	// ... uses useAutocomplete and chatState ...
</script>

<div class="composer-container">
	{#if ac.visible}<!-- ... dropdown ... -->{/if}
	<form onsubmit={handleSend}>
		<div class="composer-input">
			<!-- ... chips ... -->
			<input ... />
			<!-- ... settings toggle ... -->
		</div>
		<!-- ... settings panel ... -->
	</form>
</div>

<style>
	/* ... styles from [id]/+page.svelte ... */
</style>
```

- [ ] **Step 2: Commit**
Run: `git add frontend/src/lib/Composer.svelte && git commit -m "feat: create unified Composer component"`

---

### Task 4: Route Consolidation (Unified Root)

- [ ] **Step 1: Create IdentityForm component**
Create: `frontend/src/lib/IdentityForm.svelte` (Move content from `routes/+page.svelte`)

- [ ] **Step 2: Create ChatHero component**
Create: `frontend/src/lib/ChatHero.svelte` (Move content from `routes/chats/+page.svelte`)

- [ ] **Step 3: Refactor root route**
Modify: `frontend/src/routes/+page.svelte`
```svelte
<script lang="ts">
	import IdentityForm from '$lib/IdentityForm.svelte';
	import ChatHero from '$lib/ChatHero.svelte';
	import { chatState } from '$lib/chat-state.svelte';
</script>

{#if !chatState.userName}
	<IdentityForm />
{:else}
	<ChatHero />
{/if}
```

- [ ] **Step 4: Cleanup /chats route**
Run: `rm frontend/src/routes/chats/+page.svelte`

- [ ] **Step 5: Commit**
Run: `git add . && git commit -m "refactor: unify root route and consolidate home/identity pages"`

---

### Task 5: Mobile UX & Polish

- [ ] **Step 1: Update Sidebar with Backdrop and Close button**
Modify: `frontend/src/routes/+layout.svelte` (Add backdrop and close btn in mobile view)

- [ ] **Step 2: Final Verification**
Run: `pnpm test && pnpm playwright test`

- [ ] **Step 3: Commit**
Run: `git add . && git commit -m "ui: improve mobile sidebar navigation and accessibility"`
