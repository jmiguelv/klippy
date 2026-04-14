# Klippy AI Agent Guidelines

This document outlines the coding standards and operational mandates for AI agents working on the Klippy project.

## 🛠️ Coding Standards

- **TDD First:** Use Red/Green Test-Driven Development for all logic. Every feature or fix must have a corresponding test.
- **Simplicity:** Prefer simple solutions over complicated ones. Avoid over-engineering.
- **Functional Style:** Prefer functional programming paradigms over OOP where possible. Code should be readable and composable.
- **Fail-Fast:** Prefer throwing errors or returning Error objects over silent fallbacks or default values. Let it crash visibly if it's an impossible state.
- **Explicit Error Handling:** Never swallow exceptions. Log or propagate every caught error.
- **Documentation:** Use docstrings for all public methods and modules. Comments are only needed if the code isn't self-explanatory.
- **Type Safety:** Use strict typing (Python type hints, TypeScript strict mode).

## 🌳 Git & Workflow

- **Conventional Commits:** Use the [Conventional Commits](https://www.conventionalcommits.org/) specification.
- **Atomic Commits:** Commit small, logical units of work frequently.
- **Branching:** Use `main` and `develop` branches. Feature branches should follow conventional names (e.g., `feat/...`, `fix/...`).

## 🤖 AI Interaction Mandates

- **Concise Communication:** Provide just the code and brief reasoning. Avoid lengthy preambles or postambles.
- **Ask Before Proceeding:** If a requirement or technical path is ambiguous, stop and ask for clarification.
- **Research -> Strategy -> Execution:** Always research the codebase before proposing a plan.
- **Tool Usage:** Prefer `uv run` for Python tasks and `pnpm` for frontend tasks.

## 📁 Project Context

- **Data Hierarchy:** All harvested data lives in `data/raw/`.
- **RAG Stack:** LlamaIndex, Qdrant, FastAPI, Redis, Astro.
- **Observability:** Arize Phoenix must remain integrated for all RAG operations.
