# Implementation Plan: Code Review Fixes (Backend & Harvester)

## Objective
Apply fixes identified during the code review to bring the `backend` and `harvester` components into full compliance with `AGENTS.md`. Key focuses: removing inline imports, fixing swallowed exceptions, and improving type safety.

## Key Files & Context
- `backend/engine.py`: Fix inline imports, add missing type hints.
- `backend/main.py`: Refactor duplicated logic, add missing type hints.
- `harvester/orchestrator.py`: Stop swallowing exceptions, add type hints.
- `harvester/github/client.py`: Remove inline import.
- `harvester/main.py`: Add type hints to logging and main.
- `harvester/clickup/client.py`: Improve type hints.

## Implementation Steps

### 1. Fix Inline Imports
- **`backend/engine.py`**:
  - Move `from llama_index.core.postprocessor import SimilarityPostprocessor` to top-level.
  - Move `import time` to top-level (if not already there).
- **`harvester/github/client.py`**:
  - Move `import logging` to top-level and initialize logger at module level.

### 2. Stop Swallowing Exceptions
- **`harvester/orchestrator.py`**:
  - Replace `except Exception: pass` with `except Exception as e: logger.warning(...)` to ensure observability while allowing the loop to continue.

### 3. Improve Type Safety
- **`backend/engine.py`**:
  - Update all method signatures with proper type hints (args and return types).
  - Use `int | None` instead of `int = None`.
- **`backend/main.py`**:
  - Add type hints to `_run_ingestion`.
- **`harvester/` (all files)**:
  - Add missing type hints to constructors, methods, and return types. Use `typing` module for complex types if necessary.

### 4. Refactor for Simplicity & Deduplication
- **`backend/main.py`**:
  - Extract the source node metadata mapping logic from `query_klippy` and `query_klippy_stream` into a single helper function `format_sources(source_nodes: list) -> list[dict]`.
- **`backend/engine.py`**:
  - Extract YAML frontmatter parsing into a pure helper function outside the `KlippyEngine` class.

### 5. Cleanup
- Remove docstrings that only describe "what" a method does if the method name is self-explanatory.

## Verification & Testing
- Run backend tests: `cd backend && uv run pytest`
- Run harvester tests: `cd harvester && uv run pytest`
- Verify that Arize Phoenix tracing still works by checking logs for `set_global_handler`.
