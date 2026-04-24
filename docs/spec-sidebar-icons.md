# Spec: feat/sidebar-icons

## Goal

Replace the current fully-hidden collapsed sidebar with an icon-only rail (~56px wide), so the user always has a visual anchor for navigation. When expanded, the sidebar shows the full session list with title and action buttons — unchanged from today.

Reference pattern: [shadcn-svelte Sidebar](https://shadcn-svelte.com/docs/components/sidebar).

---

## Current behaviour (baseline)

File: `frontend/src/routes/chats/+layout.svelte`

- `let isSidebarOpen = $state(false)` — starts closed.
- Closed state: `.sidebar.closed { margin-left: -280px }` — sidebar is fully off-screen.
- Toggle button: `.sidebar-toggle` floats at `top: 20px; left: 20px` inside `.chat-content`.
- Mobile (≤768px): sidebar switches to `position: fixed`, slides in/out with `translateX(-100%)`.

---

## Proposed behaviour

### Desktop (>768px)

| State     | Sidebar width | What shows in sidebar                  |
|-----------|---------------|----------------------------------------|
| Collapsed | 56px          | `<MessageSquare>` icon per session     |
| Expanded  | 280px         | Full title + Pencil/Trash action icons |

The toggle button moves **into the sidebar** at the bottom of the session list (or top of the header), so it's always reachable regardless of sidebar state.

### Mobile (≤768px)

No change from current behaviour — overlay/drawer at `position: fixed` with backdrop. The icon rail is a desktop-only pattern.

---

## State and persistence

```ts
// Replace the current boolean with a state that loads from localStorage
let isSidebarOpen = $state(
  typeof localStorage !== 'undefined'
    ? localStorage.getItem('klippy_sidebar_open') !== 'false'
    : false
);

// Keep in sync
$effect(() => {
  localStorage.setItem('klippy_sidebar_open', String(isSidebarOpen));
});
```

Default: `false` (collapsed on first visit). The `!== 'false'` check means the key being absent also evaluates to `true` — if you want collapsed as default, use `=== 'true'` instead. Choose one and be consistent.

---

## Template changes

### Session items in collapsed state

When collapsed, each `.session-item` should:
- Hide `.session-title` and `.session-actions`.
- Show only the `<MessageSquare>` icon, centred.
- Use the `title` HTML attribute for the session name (browser tooltip on hover).

```svelte
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
```

### Sidebar header in collapsed state

When collapsed, the header should collapse to show only the toggle:

```svelte
<header class="sidebar-header">
  {#if isSidebarOpen}
    <div class="wordmark-wrap">
      <span class="sidebar-wordmark">Chats</span>
    </div>
    <button class="new-chat-btn" onclick={newChat}>
      <Plus size={16} />
      <span>New Chat</span>
    </button>
  {/if}
  <button
    class="sidebar-toggle-inside"
    onclick={() => (isSidebarOpen = !isSidebarOpen)}
    title="Toggle Sidebar"
    aria-label={isSidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
  >
    {#if isSidebarOpen}<ChevronLeft size={16} />{:else}<ChevronRight size={16} />{/if}
  </button>
</header>
```

Remove the existing floating `.sidebar-toggle` button from `.chat-content` — it is no longer needed because the toggle lives inside the sidebar.

When collapsed, the New Chat action is hidden. Consider adding a `+` icon-only button at the bottom of the session list in collapsed state, or accept that users must expand to create a new chat.

---

## CSS changes

### Sidebar width transition

Replace `margin-left` toggle with `width` transition:

```css
.sidebar {
  width: 280px;
  /* remove: margin-left transition */
  transition: width 0.25s ease;
  overflow: hidden; /* prevents content from spilling during transition */
}

.sidebar.closed {
  width: 56px;
  /* remove: margin-left: -280px */
}
```

### Session items when collapsed

```css
.sidebar.closed .session-item {
  justify-content: center;
  padding: var(--size-2);
}

.sidebar.closed :global(.session-icon) {
  opacity: 0.6;
}
```

### Sidebar header when collapsed

```css
.sidebar.closed .sidebar-header {
  align-items: center;
  padding: var(--size-3) var(--size-2);
}
```

### Toggle button (now inside sidebar)

```css
.sidebar-toggle-inside {
  align-self: flex-end;
  background: none;
  border: none;
  cursor: pointer;
  padding: var(--size-2);
  color: var(--ink-2);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.15s;
}

.sidebar-toggle-inside:hover {
  color: var(--ink-0);
}
```

### Remove floating toggle CSS

Delete `.sidebar-toggle` and its rules — it becomes dead CSS once removed from the template.

### Mobile: revert to overlay

At `≤768px`, the icon rail is not appropriate. The mobile styles must restore the `translateX` behaviour and hide the icon rail:

```css
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    width: 280px; /* always full-width on mobile */
    height: 100%;
    z-index: 200;
  }

  .sidebar.closed {
    width: 280px; /* override the 56px desktop rule */
    transform: translateX(-100%);
  }

  /* ... existing backdrop and sidebar-close styles unchanged ... */
}
```

---

## Testing

1. Load `/chats/` — sidebar should be collapsed to a 56px rail showing `MessageSquare` icons per session.
2. Hover a session icon → browser tooltip shows the session title.
3. Click a session icon → navigates to that session.
4. Click the toggle (chevron inside sidebar header) → sidebar expands to 280px, titles appear.
5. Collapse again — width animates smoothly, no layout jump.
6. Refresh — sidebar state is restored from `localStorage`.
7. At 768px or below (DevTools mobile emulation): sidebar becomes an overlay — no icon rail.
8. Run `pnpm check` — no type errors.

## Branch

`feat/sidebar-icons`
