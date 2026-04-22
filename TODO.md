# TODO

Items identified from code review (2026-04-20).

## High priority

- [x] **`fix/hardcoded-api-url`** — replace hardcoded `http://localhost:8000` in `frontend/src/routes/explore/+page.svelte` with a `PUBLIC_API_URL` env var
- [x] **`test/engine-chat-coverage`** — add tests to `backend/tests/test_engine.py` for chat mode, session history persistence, and `MetadataFilters` application

## Medium priority

- [x] **`refactor/engine-history`** — reverted in `fix/chat-history-continuity`; explicit construction is correct
- [x] **`feat/autocomplete-offline-indicator`** — show a subtle indicator in the frontend when the metadata/stats cache fails to populate (backend unreachable)

