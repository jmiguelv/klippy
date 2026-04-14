# Implementation Plan: Enterprise Search Aggregator (RAG)

## Objective
To build a Retrieval-Augmented Generation (RAG) based search aggregator for internal company use. The system will ingest, index, and query data from ClickUp (project management) and GitHub (source code and history) to answer complex natural language questions like "What is project X about?", "What has been happening in project Y?", and "Have we done anything similar to Z?".

## Background & Motivation
Currently, company knowledge is siloed between project management tools (ClickUp) and source control (GitHub). A unified search interface is required to enable employees to discover context, history, and relationships across these platforms quickly and efficiently using natural language.

## Functional Requirements
1.  **FR1 (Data Ingestion - ClickUp):** The system must authenticate with the ClickUp API and periodically extract tasks, comments, and project structures.
2.  **FR2 (Data Ingestion - GitHub):** The system must authenticate with the GitHub API and periodically extract repository metadata, commit history, pull requests, and relevant source code.
3.  **FR3 (Data Transformation):** The system must convert all ingested data into structured Markdown format to maintain context and structure for the LLM.
4.  **FR4 (Indexing & Vectorization):** The system must chunk Markdown documents into appropriate sizes and generate vector embeddings using an embedding model.
5.  **FR5 (Hybrid Search):** The system must support querying the vector database using both semantic similarity (vectors) and keyword/metadata filtering (e.g., date, source platform).
6.  **FR6 (RAG Generation):** The system must pass the retrieved context and user query to an LLM to generate a synthesized, natural language answer.
7.  **FR7 (Source Citation):** The generated answer must include direct, clickable links (citations) to the original ClickUp task or GitHub resource.
8.  **FR8 (Search Interface):** The frontend must provide a simple text input field for users to enter natural language queries and a display area for the synthesized results.
9.  **FR9 (Incremental Sync):** The data harvesters must support incremental syncing, ensuring only data created or modified since the last successful run is fetched and indexed.

## Coding Standards & CI/CD
To ensure codebase quality and consistency, the following standards will be strictly enforced:

1.  **Python Backend & Harvesters:**
    *   **Linting & Formatting:** `Ruff` will be used for extremely fast linting and formatting.
    *   **Testing:** `Pytest` will be the primary testing framework for unit and integration tests.
2.  **Astro Frontend:**
    *   **TypeScript:** Strict type checking (`tsconfig.json` strict mode).
    *   **Linting:** `ESLint`.
    *   **Formatting:** `Prettier`.
3.  **CI/CD & Automation:**
    *   **GitHub Actions:** Automate Ruff, Pytest, ESLint, and TypeScript checks on every PR and push.
4.  **Development Methodology & Style:**
    *   **TDD:** Red/green Test-Driven Development is strictly required.
    *   **Paradigm:** Prefer a functional programming style over Object-Oriented Programming (OOP) whenever possible. Code should be readable and composable, avoiding over-engineering (simple over complicated).
    *   **Documentation:** Use comments only when code is not self-explanatory; Docstrings are required.
5.  **Error Handling (Fail-Fast):**
    *   Prefer returning or throwing errors over silent fallbacks or default values.
    *   Never swallow errors — log or propagate every caught exception.
    *   No defensive fallback logic for cases that "shouldn't happen" — let the application crash visibly so the root cause is obvious.
6.  **Version Control & Workflow:**
    *   **Commits:** Strict adherence to Conventional Commits.
    *   **Branches:** Branch names must mirror conventional commits (e.g., `feat/...`, `fix/...`). The workflow consists of `main` and `develop` branches.
7.  **AI/Agent Interaction Guidelines:**
    *   Provide concise communication: just the code and brief reasoning, no lengthy explanations unless explicitly requested.
    *   If any requirement or step is unclear, ask for clarification before proceeding.

## Proposed Solution & Architecture

The system will be composed of four primary components:

1.  **Data Harvester (Cron + Python Scripts):**
    *   **ClickUp:** Scheduled Python scripts will incrementally extract tasks, comments, and project metadata via the ClickUp API, converting them into structured Markdown documents.
    *   **GitHub:** Scheduled scripts will pull repository metadata, commit histories, Pull Requests, and relevant source code via the GitHub API.
    *   *Mechanism:* Cron jobs will trigger these scripts periodically (e.g., hourly or daily).

2.  **Backend & Indexing (Docker Compose + FastAPI + LlamaIndex + Qdrant):**
    *   **Orchestration:** The entire backend stack (FastAPI, Qdrant, Redis) will be orchestrated and run using **Docker Compose**.
    *   **Processing:** LlamaIndex will orchestrate data loading, chunking (splitting Markdown/code into manageable pieces), and embedding generation (e.g., using OpenAI or local embeddings).
    *   **Storage:** Qdrant will serve as the vector database, storing embeddings and rich metadata to support powerful hybrid search (combining semantic similarity with keyword filtering).
    *   **API:** A FastAPI service will expose endpoints (e.g., `/api/search`) to handle incoming queries, execute the LlamaIndex retrieval pipeline, and stream LLM responses back to the client.

3.  **Frontend (Astro):**
    *   A fast, lightweight web application built with Astro.
    *   Provides a clean, intuitive search interface (text box) where users can submit natural language queries.
    *   Displays the LLM-synthesized answer along with citations/links back to the original ClickUp tasks or GitHub repositories.

4.  **Observability & Caching:**
    *   **Observability:** Integration with tools like Arize Phoenix or LangSmith to trace LlamaIndex executions, monitor retrieval quality (precision/recall), and track LLM token usage. Standard Python logging for backend and harvester errors.
    *   **Caching:** Redis (orchestrated via Docker Compose) will cache exact or semantically similar queries to reduce LLM API costs and improve response latency.

## Implementation Steps

### Phase 1: Foundation & Data Harvesting
1.  **Repository Setup:** Initialize the monorepo structure (e.g., `harvester/`, `backend/`, `frontend/`). Ensure `main` and `develop` branches are created.
2.  **ClickUp Harvester:** Develop a Python script to authenticate with ClickUp, fetch tasks/comments from specific spaces/folders, format them as Markdown, and save them locally or push to a staging area. Implement incremental syncing.
3.  **GitHub Harvester:** Develop a Python script to authenticate with GitHub, fetch repository metadata, recent commits, PRs, and specific file types. Save as Markdown. Implement incremental syncing.
4.  **Scheduler Setup:** Configure basic Cron jobs to run the harvesters on a defined schedule.

### Phase 2: Backend & Vector Database (Docker Compose)
1.  **Docker Compose Setup:** Create a `docker-compose.yml` file to orchestrate the backend services:
    *   FastAPI backend service.
    *   Qdrant vector database container.
    *   Redis caching container.
2.  **LlamaIndex Integration:** Set up LlamaIndex pipelines within the FastAPI app to:
    *   Load the Markdown files generated by the harvesters.
    *   Chunk the documents appropriately.
    *   Generate embeddings and insert them into Qdrant along with relevant metadata.
3.  **FastAPI Development:** Build the `/api/search` endpoint. This endpoint will take a query, use LlamaIndex to perform a hybrid search against Qdrant, pass the retrieved context to an LLM, and return the synthesized answer with sources.
4.  **Caching Layer:** Implement a basic caching mechanism for identical queries in FastAPI using the Redis container to bypass the LLM step when possible.

### Phase 3: Frontend Interface
1.  **Astro Setup:** Initialize an Astro project.
2.  **Search UI:** Build a simple, clean search interface with a text input.
3.  **API Integration:** Connect the frontend to the FastAPI `/api/search` endpoint (running via Docker Compose).
4.  **Results Display:** Render the LLM's response, formatting Markdown appropriately, and distinctly displaying clickable links to the source ClickUp tasks or GitHub URLs.

### Phase 4: Observability & Refinement
1.  **Tracing Integration:** Integrate an observability tool (e.g., LangSmith) into the LlamaIndex pipeline to monitor query performance and retrieval quality.
2.  **Logging:** Ensure robust logging across the harvester and FastAPI services.
3.  **Prompt Tuning:** Refine the system prompt provided to the LLM to ensure answers are concise, accurate, and properly cite sources.

## Verification & Testing
*   **Unit Tests:** TDD principles applied for the data extraction parsing logic.
*   **Integration Tests:** Verify the FastAPI endpoints correctly query Qdrant and return valid JSON responses. Run tests against the Docker Compose stack.
*   **Manual End-to-End Testing:**
    *   Run the harvester to ingest sample ClickUp and GitHub data.
    *   Submit a query via the Astro frontend like "What is the status of the authentication feature?".
    *   Verify the LLM returns a correct summary based on the ingested data and provides accurate links.

## Migration & Rollback (Not applicable for V1)
As this is a greenfield project, no complex migration is required. Rollback involves reverting to previous Git commits.