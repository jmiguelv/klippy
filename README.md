# Klippy 📎

An Enterprise Search Aggregator and RAG (Retrieval-Augmented Generation) system that unified company knowledge from ClickUp and GitHub.

## 🚀 Overview

Klippy automates the harvesting of project management data and source code history, indexing it into a high-performance vector database to answer natural language questions like:
- *"What is project X about?"*
- *"What has been happening in project Y recently?"*
- *"Have we implemented a feature similar to Z before?"*

## 🏗️ Architecture

- **Data Harvester:** A parallelized Python engine that incrementally pulls tasks, documents, and pages from ClickUp, alongside repositories, commits, and READMEs from GitHub.
- **Backend (FastAPI + LlamaIndex):** Orchestrates the RAG pipeline, performing hybrid search against Qdrant and synthesizing answers using OpenAI-compatible LLMs.
- **Vector Store (Qdrant):** Stores high-dimensional embeddings and rich metadata.
- **Cache (Redis):** Provides low-latency responses for frequent queries.
- **Observability (Arize Phoenix):** Real-time tracing of retrieval and synthesis for debugging and evaluation.
- **Frontend (Astro):** A fast, minimal search interface.

## 🛠️ Setup

### Prerequisites
- Docker & Docker Compose
- LLM API Key (OpenAI or compatible)
- ClickUp API Key & Workspace ID
- GitHub Personal Access Token (Fine-grained)

### Configuration
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Fill in your credentials and model preferences.

### Launch
```bash
docker compose up --build
```

## 📖 Usage

- **Search Interface:** [http://localhost:4321](http://localhost:4321)
- **API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Tracing & Traces:** [http://localhost:6006](http://localhost:6006)

## 🧪 Development

### Harvester
Uses `uv` for management and `pytest` for TDD.
```bash
cd harvester
uv run pytest
```

### Backend
FastAPI with strict type checking and LlamaIndex.
```bash
cd backend
uv run pytest
```
