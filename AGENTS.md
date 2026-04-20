# Klippy AI Agent Guidelines

This document outlines the coding standards and operational mandates for AI agents working on the Klippy project.

## Coding Standards

- **TDD:** Write a failing test first, then the minimum code to pass it. Never write implementation without a corresponding test.
- **Simplicity:** Simple over complicated. No abstractions for hypothetical future needs.
- **Functional style:** Prefer pure functions and immutable data over OOP where the language allows.
- **Fail fast:** Validate at system boundaries. Never swallow exceptions — log or propagate every caught error.
- **No comments** unless the WHY is non-obvious. No docstrings on self-explanatory methods.
- **Type safety:** Python type hints throughout; TypeScript strict mode in the frontend.

## Git & Workflow

- **Conventional Commits:** Use the [Conventional Commits](https://www.conventionalcommits.org/) specification.
- **Branching:** `main` is the only long-lived branch. Branch off `main` using conventional commit prefixes (`feat/`, `fix/`, `chore/`, `docs/`, `refactor/`, `perf/`) — kebab-case, ≤40 chars. Push and open a PR.
- **Atomic commits:** Commit small, logical units of work.

## AI Interaction

- Concise communication: code and brief reasoning only. No lengthy preambles.
- Ask before proceeding if a requirement or technical path is ambiguous.
- Research the codebase before proposing changes.
- Run tests after every change and fix failures before committing.
- Prefer `uv run` for Python tasks and `pnpm` for frontend tasks.

## Project Context

- **Stack:** FastAPI, LlamaIndex, Qdrant, Redis, SvelteKit (Svelte 5), Docker Compose.
- **Data:** All harvested markdown lives in `data/raw/` (gitignored).
- **Observability:** Arize Phoenix is integrated for RAG tracing — keep it wired up.
- **Config:** System prompt lives in `config/prompt.md`.
