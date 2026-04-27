# Spec: feat/mobile-responsiveness

## Goal

Make the Klippy UI usable on screens narrower than 640px. The current layout assumes a desktop-width viewport; this spec covers the adjustments needed for mobile without altering the desktop experience.

## Breakpoint

Single breakpoint: `@media (max-width: 640px)` applied in each component's `<style>` block. No new shared stylesheet — keep styles co-located with their components.

---

## Component changes

### Sidebar — `frontend/src/routes/chats/+layout.svelte`

The sidebar already switches to `position: fixed` at `≤768px`, which is the right behaviour. The remaining gap is:

- **Backdrop tap-to-close**: already implemented via `onclick={() => (isSidebarOpen = false)}` on `.sidebar-backdrop`. No change needed.
- **Hamburger always visible**: `.sidebar-toggle` is currently `position: absolute; top: 20px; left: 20px`. On mobile, when the sidebar is open, the toggle is obscured by the sidebar. The sidebar header already has a `.sidebar-close` button (visible at `≤768px`) so the toggle itself can remain as-is — just ensure it has adequate tap target size (already 32×32).
- **Reduce sidebar header padding** at `≤640px`: `var(--size-4)` → `var(--size-3)` so it doesn't feel oversized.

```css
@media (max-width: 640px) {
  .sidebar-header {
    padding: var(--size-3);
  }
}
```

### Chat content area — `frontend/src/routes/chats/+layout.svelte`

The `.chat-content` flex child takes the remaining width. No structural change needed — it naturally fills after the sidebar collapses off-screen.

---

### Composer — `frontend/src/routes/chats/[id]/+page.svelte`

The composer sits at the bottom of the conversation page. Key issues at narrow widths:

- **Padding**: `.composer-input` uses `var(--size-6)` horizontal padding. Reduce to `var(--size-3)` on mobile.
- **Hint row**: `.composer-hint` keyboard shortcuts are not critical on mobile. Hide it to reclaim vertical space.
- **Filter chips**: `.filter-chips` needs `flex-wrap: wrap` to prevent overflow (already done per `fix/filter-chip-overflow`). Verify chips don't exceed composer width.
- **Settings panel**: `.settings-panel` uses fixed widths; ensure it doesn't overflow. Apply `width: 100%` and `max-width: none` at mobile.

```css
@media (max-width: 640px) {
  .composer-input {
    padding: var(--size-3);
  }

  .composer-hint {
    display: none;
  }

  .settings-panel {
    width: 100%;
    max-width: none;
    right: 0;
    left: 0;
  }
}
```

The same composer structure is used on the `/chats` hero page (`frontend/src/routes/chats/+page.svelte`). Apply the same overrides there.

---

### Chat bubbles — `frontend/src/routes/chats/[id]/+page.svelte`

Current `.bubble` has `padding: var(--size-4) var(--size-6)` and fixed `max-width: 800px`. On mobile:

- Remove the `max-width` constraint (or set it to `100%`) so bubbles fill the viewport.
- Reduce padding to `var(--size-3) var(--size-4)`.
- The `.bubble-meta` row (model, timing) can be hidden — it's debug information, not user-facing.

```css
@media (max-width: 640px) {
  .bubble {
    max-width: 100%;
    padding: var(--size-3) var(--size-4);
  }

  .bubble-meta {
    display: none;
  }
}
```

---

### Retrieval steps — `frontend/src/routes/chats/[id]/+page.svelte`

`.retrieval-steps` renders the chain-of-thought steps (search → rerank → synthesise). On mobile, the step labels and timing are noise.

- Hide `.step-label` text, keep the icon.
- Reduce step item padding.
- Stack `.step-item` elements vertically with a smaller gap.

Current structure:
```
.retrieval-steps
  .step-item
    .step-icon   (Search/Code/FileText icon)
    .step-label  ("Searching…")
    .step-timing
```

```css
@media (max-width: 640px) {
  .retrieval-steps {
    gap: var(--size-1);
    flex-direction: column;
  }

  .step-label,
  .step-timing {
    display: none;
  }

  .step-item {
    padding: var(--size-1) var(--size-2);
  }
}
```

---

### Source cards — `frontend/src/routes/chats/[id]/+page.svelte`

`.source-grid` is a multi-column grid. On mobile, collapse to single column.

```css
@media (max-width: 640px) {
  .source-grid {
    grid-template-columns: 1fr;
  }

  .source-card {
    padding: var(--size-3);
  }

  .source-title {
    font-size: 0.85rem;
  }

  .source-meta {
    font-size: 0.7rem;
  }
}
```

---

### Hero page — `frontend/src/routes/chats/+page.svelte`

- `.empty-greeting` / `.empty-heading` already use `clamp()` for font size — no change needed.
- `.empty-description` `max-width: 480px` is fine; on narrow screens it auto-constrains.
- Ensure `.hero-section` padding doesn't cause horizontal scroll: `padding: var(--size-4)` at mobile (currently `var(--size-8)` bottom only).

```css
@media (max-width: 640px) {
  .hero-section {
    padding: var(--size-4);
  }
}
```

---

## Testing

1. Open Chrome DevTools → toggle device toolbar → iPhone SE (375px wide).
2. Navigate to `/` — identity card should be readable with no horizontal scroll.
3. Navigate to `/chats/` — hero text readable, composer full-width.
4. Open a chat session. Verify:
   - Composer fills the width with adequate tap targets.
   - Bubbles are full-width.
   - Source cards stack vertically.
   - Retrieval steps collapse to icons.
5. Open and close the sidebar via the toggle — backdrop appears, tap-to-close works.
6. Rotate to landscape (667×375 effectively) — layout should still be usable.
7. Run `pnpm check` — no new type errors.

## Branch

`feat/mobile-responsiveness`
