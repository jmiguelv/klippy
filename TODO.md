# TODO

Items identified from code review (2026-04-20).

## High priority

L7: - [x] **`fix/hardcoded-api-url`** — replace hardcoded `http://localhost:8000` in `frontend/src/routes/chats/+page.svelte` with a `PUBLIC_API_URL` env var

- [x] **`test/engine-chat-coverage`** — add tests to `backend/tests/test_engine.py` for chat mode, session history persistence, and `MetadataFilters` application

## Medium priority

- [x] **`refactor/engine-history`** — reverted in `fix/chat-history-continuity`; explicit construction is correct
- [x] **`feat/autocomplete-offline-indicator`** — show a subtle indicator in the frontend when the metadata/stats cache fails to populate (backend unreachable)
- [x] **`fix/filter-chip-overflow`** — long filter values cause chips to overflow the composer width; add `max-width` and horizontal scroll to `.filter-chips` (and `.bubble-filters` in the message bubble)
- [x] **`fix/session-action-icons-dark-mode`** — rename and delete icons in the session list are not visible in dark mode; `.session-actions button` colour needs to inherit from `--ink-2` rather than a fixed value
- [x] **`feat/chats-id-routing`** — URL-per-session routing with `/chats/[id]/`; shared session state in `chat-state.svelte.ts`; sidebar in `chats/+layout.svelte`
- [x] **`feat/identity-page`** — `/` identity page with typeahead seeded from `creator`/`assignee` fields; personalised `/chats` hero; user name in nav
- [ ] **`feat/mobile-responsiveness`** — general mobile layout pass: composer, chat bubbles, retrieval steps, and source cards need responsive sizing and spacing adjustments below 640px
- [ ] **`feat/sidebar-icons`** — redesign sidebar to show icon-only view when collapsed, similar to shadcn-svelte sidebar pattern (https://shadcn-svelte.com/docs/components/sidebar); each session item shows a chat icon when collapsed, expanding to show the full title
- [x] **`feat/questions-endpoint`** — implement `/questions` backend endpoint using `QuestionsAnsweredExtractor` on ingestion; store in Qdrant metadata; frontend fetches and rotates as placeholder chips

