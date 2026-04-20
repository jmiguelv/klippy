# Klippy — Gemini Agent Guidelines

## Project overview

Klippy is a RAG-based enterprise search aggregator. It ingests ClickUp tasks/docs and GitHub markdown files, indexes them into Qdrant via LlamaIndex, and exposes a chat interface through a FastAPI backend and SvelteKit frontend.

Stack: Python (uv), FastAPI, LlamaIndex, Qdrant, Redis, SvelteKit (Svelte 5), Docker Compose.

## Coding standards

- **TDD:** Write a failing test first, then the minimum code to pass it. Never write implementation without a corresponding test.
- **Simplicity:** Simple over complicated. No abstractions for hypothetical future needs.
- **Functional style:** Prefer pure functions and immutable data over OOP where the language allows.
- **Fail fast:** Validate at system boundaries. Never swallow exceptions — log or propagate every caught error.
- **No comments** unless the WHY is non-obvious. No docstrings on self-explanatory methods.
- **Type safety:** Python type hints throughout; TypeScript strict mode in the frontend.

## Commands

```bash
# Python (backend or harvester)
uv run pytest          # run tests
uv run python main.py  # run scripts

# Frontend
pnpm dev               # dev server
pnpm build             # production build
pnpm test              # unit tests

# Infrastructure
docker compose up -d   # start all services
```

## Git workflow

- Branch naming mirrors conventional commit types: `feat/`, `fix/`, `chore/`, `docs/`, `refactor/`, `perf/` — kebab-case, ≤40 chars.
- `main` is the only long-lived branch. Always branch off `main`, then push and open a PR.
- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/): `<type>(<scope>): <description>`.

## Repository layout

```
backend/        FastAPI app, LlamaIndex engine, Qdrant/Redis integration
harvester/      ClickUp and GitHub ingestion scripts
frontend/       SvelteKit UI (Svelte 5)
config/         System prompt and runtime config
data/raw/       Harvested markdown files (gitignored)
docker-compose.yml
```

## AI interaction

- Concise communication: code and brief reasoning only.
- Ask before proceeding if a requirement is ambiguous.
- Research the codebase before proposing changes.
- Run tests after every change and fix failures before committing.
