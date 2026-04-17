import os
import re
import json
import logging
import argparse
import uuid
from collections import Counter
from contextlib import asynccontextmanager
from datetime import datetime

import uvicorn
import redis
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from engine import KlippyEngine
from llama_index.core import set_global_handler
from llama_index.core.base.llms.types import ChatMessage

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend.main")

# Arize Phoenix Observability via OpenInference (OTLP)
phoenix_endpoint = os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "http://phoenix:6006")
if not phoenix_endpoint.endswith("/v1/traces"):
    phoenix_endpoint = f"{phoenix_endpoint}/v1/traces"

set_global_handler("arize_phoenix", endpoint=phoenix_endpoint)


class QueryRequest(BaseModel):
    text: str
    session_id: str = None


class QueryResponse(BaseModel):
    answer: str
    session_id: str
    sources: list[dict] = []
    total_time_ms: int = 0
    cached_at: str = None
    context_length: int = 0


class IngestRequest(BaseModel):
    limit: int = None
    force: bool = False


class FeedbackRequest(BaseModel):
    session_id: str
    is_positive: bool


# Redis for Caching and Memory
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True,
)

# Engine initialization
engine = KlippyEngine(
    qdrant_host=os.getenv("QDRANT_HOST", "localhost"),
    data_dir=os.getenv("DATA_DIR", "/app/data/raw"),
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Backend started. Ingestion must be triggered manually.")
    yield


app = FastAPI(lifespan=lifespan, title="Klippy Backend API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_history_from_redis(session_id: str) -> list[ChatMessage]:
    """Retrieves and deserializes chat history from Redis."""
    history_json = redis_client.get(f"chat_history:{session_id}")
    if not history_json:
        return []

    try:
        raw_history = json.loads(history_json)
        history = []
        for m in raw_history:
            role = m.get("role") or m.get("MessageRole")
            content = m.get("content") or m.get("text") or ""
            if role:
                history.append(ChatMessage(role=role, content=content))
        return history
    except Exception as e:
        logger.error(f"Failed to parse chat history for {session_id}: {e}")
        return []


def save_history_to_redis(session_id: str, history: list[dict]):
    """Serializes and saves chat history to Redis."""
    redis_client.setex(f"chat_history:{session_id}", 3600 * 24, json.dumps(history))


@app.post("/query", response_model=QueryResponse)
async def query_klippy(request: QueryRequest):
    session_id = request.session_id or str(uuid.uuid4())

    try:
        now = datetime.now().isoformat()

        chat_history = get_history_from_redis(session_id)
        response_obj = engine.chat(request.text, chat_history=chat_history)
        answer = str(response_obj)

        updated_history = [m.dict() for m in chat_history]
        updated_history.append({"role": "user", "content": request.text})
        updated_history.append({"role": "assistant", "content": answer})
        save_history_to_redis(session_id, updated_history)

        # Extract sources from node metadata (frontmatter fields are indexed there, not in text)
        sources = []
        context_length = 0
        for node in response_obj.source_nodes:
            text = node.node.get_text()
            context_length += len(text)
            metadata = node.node.metadata

            title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
            sources.append(
                {
                    "source": metadata.get("source", "unknown"),
                    "url": metadata.get("url"),
                    "title": title_match.group(1)
                    if title_match
                    else metadata.get("file_name", "Untitled"),
                    "score": float(node.score) if node.score is not None else 0.0,
                }
            )

        return QueryResponse(
            answer=answer,
            session_id=session_id,
            sources=sources,
            total_time_ms=response_obj.metadata.get("total_time_ms", 0),
            cached_at=now,
            context_length=context_length,
        )
    except Exception as e:
        logger.error(f"Error during chat turn: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/feedback")
async def process_feedback(request: FeedbackRequest):
    if not request.is_positive:
        redis_client.delete(f"chat_history:{request.session_id}")
        logger.info(
            f"Cleared chat history for session due to negative feedback: {request.session_id}"
        )
    return {"status": "Feedback received"}


@app.post("/ingest")
async def trigger_ingestion(request: IngestRequest, background_tasks: BackgroundTasks):
    """Triggers a manual ingestion. Can optionally limit number of docs and force re-index."""
    background_tasks.add_task(
        engine.ingest_data, limit=request.limit, force=request.force
    )
    return {
        "status": "Ingestion task started in background",
        "limit": request.limit,
        "force": request.force,
    }


@app.get("/debug/stats")
async def collection_stats(field: str = "type"):
    """Returns value counts for a metadata field across all indexed nodes."""
    counts: Counter = Counter()
    offset = None

    while True:
        result, offset = engine.client.scroll(
            collection_name=engine.collection_name,
            limit=1000,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        for point in result:
            payload = point.payload or {}
            # LlamaIndex may store metadata as top-level keys or inside _node_content
            if field in payload:
                counts[str(payload[field])] += 1
            elif "_node_content" in payload:
                try:
                    content = json.loads(payload["_node_content"])
                    value = content.get("metadata", {}).get(field)
                    if value is not None:
                        counts[str(value)] += 1
                except (json.JSONDecodeError, TypeError):
                    pass
        if offset is None:
            break

    total = sum(counts.values())
    return {"field": field, "total_nodes": total, "counts": dict(counts.most_common())}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


def main():
    parser = argparse.ArgumentParser(description="Klippy Backend and Indexer")
    parser.add_argument("--ingest", action="store_true", help="Run indexing and exit")
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of documents to ingest (random sampling)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-indexing of all documents (ignore cache)",
    )

    args, unknown = parser.parse_known_args()

    if args.ingest:
        logger.info(
            f"CLI: Starting manual ingestion (limit={args.limit}, force={args.force})..."
        )
        engine.ingest_data(limit=args.limit, force=args.force)
        logger.info("CLI: Ingestion complete. Exiting.")
    else:
        logger.info("CLI: Starting FastAPI server...")
        uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
