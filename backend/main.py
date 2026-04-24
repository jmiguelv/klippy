import os
import re
import json
import logging
import argparse
import time
import uuid
from collections import Counter, defaultdict
from contextlib import asynccontextmanager
from datetime import datetime

import uvicorn
import redis
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
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
    filters: dict[str, str] = {}
    top_k: int = 10
    similarity_cutoff: float | None = None


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
                # Handle cases where the role was serialized as 'MessageRole.USER' string
                if "." in role:
                    role = role.split(".")[-1].lower()
                history.append(ChatMessage(role=role, content=content))
        return history
    except Exception as e:
        logger.error(f"Failed to parse chat history for {session_id}: {e}")
        return []


def save_history_to_redis(session_id: str, history: list[dict]):
    """Serializes and saves chat history to Redis."""
    redis_client.setex(f"chat_history:{session_id}", 3600 * 24, json.dumps(history))


def format_sources(source_nodes: list) -> tuple[list[dict], int]:
    """Extracts sources and context length from a list of source nodes."""
    sources = []
    context_length = 0
    for node in source_nodes:
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
    return sources, context_length


@app.post("/query", response_model=QueryResponse)
async def query_klippy(request: QueryRequest):
    session_id = request.session_id or str(uuid.uuid4())

    try:
        now = datetime.now().isoformat()

        chat_history = get_history_from_redis(session_id)
        response_obj = engine.chat(
            request.text,
            chat_history=chat_history,
            filters=request.filters or None,
            top_k=request.top_k,
            similarity_cutoff=request.similarity_cutoff,
        )
        answer = str(response_obj)

        updated_history = [{"role": m.role.value, "content": m.content or ""} for m in chat_history]
        updated_history.append({"role": "user", "content": request.text})
        updated_history.append({"role": "assistant", "content": answer})
        save_history_to_redis(session_id, updated_history)

        sources, context_length = format_sources(response_obj.source_nodes)

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


@app.post("/query-stream")
async def query_klippy_stream(request: QueryRequest):
    session_id = request.session_id or str(uuid.uuid4())

    async def event_stream():
        yield f"data: {json.dumps({'type': 'meta', 'session_id': session_id, 'model': engine.llm_model})}\n\n"
        try:
            now = datetime.now().isoformat()
            chat_history = get_history_from_redis(session_id)
            start = time.time()

            streaming_response = await engine.astream_chat(
                message=request.text,
                chat_history=chat_history,
                filters=request.filters or None,
                top_k=request.top_k,
                similarity_cutoff=request.similarity_cutoff,
            )

            # Signal that retrieval is complete and LLM synthesis is starting
            num_sources = len(streaming_response.source_nodes)
            yield f"data: {json.dumps({'type': 'retrieved', 'num_sources': num_sources})}\n\n"

            answer_parts = []
            async for token in streaming_response.async_response_gen():
                answer_parts.append(token)
                yield f"data: {json.dumps({'type': 'chunk', 'text': token})}\n\n"

            answer = "".join(answer_parts)
            total_time_ms = int((time.time() - start) * 1000)

            updated_history = [{"role": m.role.value, "content": m.content or ""} for m in chat_history]
            updated_history.append({"role": "user", "content": request.text})
            updated_history.append({"role": "assistant", "content": answer})
            save_history_to_redis(session_id, updated_history)

            sources, context_length = format_sources(streaming_response.source_nodes)

            yield f"data: {json.dumps({'type': 'done', 'sources': sources, 'total_time_ms': total_time_ms, 'context_length': context_length, 'cached_at': now})}\n\n"

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'detail': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/feedback")
async def process_feedback(request: FeedbackRequest):
    if not request.is_positive:
        redis_client.delete(f"chat_history:{request.session_id}")
        logger.info(
            f"Cleared chat history for session due to negative feedback: {request.session_id}"
        )
    return {"status": "Feedback received"}


STATS_CACHE_TTL = 3600  # 1 hour

_INTERNAL_FIELDS = {
    "_node_content",
    "_node_type",
    "doc_id",
    "document_id",
    "ref_doc_id",
    "file_path",
    "file_name",
    "file_type",
    "file_size",
    "creation_date",
    "last_modified_date",
}


def invalidate_stats_cache():
    """Removes all cached debug/stats entries after ingestion."""
    for key in redis_client.scan_iter("debug_stats:*"):
        redis_client.delete(key)
    logger.info("Invalidated debug stats cache.")


def _run_ingestion(limit, force):
    engine.ingest_data(limit=limit, force=force)
    invalidate_stats_cache()


@app.post("/ingest")
async def trigger_ingestion(request: IngestRequest, background_tasks: BackgroundTasks):
    """Triggers a manual ingestion. Can optionally limit number of docs and force re-index."""
    background_tasks.add_task(_run_ingestion, limit=request.limit, force=request.force)
    return {
        "status": "Ingestion task started in background",
        "limit": request.limit,
        "force": request.force,
    }


@app.get("/debug/fields")
async def collection_fields():
    """Returns metadata field names available across indexed nodes (sampled)."""
    fields: set[str] = set()
    result, _ = engine.client.scroll(
        collection_name=engine.collection_name,
        limit=200,
        with_payload=True,
        with_vectors=False,
    )
    for point in result:
        payload = point.payload or {}
        if "_node_content" in payload:
            try:
                content = json.loads(payload["_node_content"])
                fields.update(
                    k for k in content.get("metadata", {}) if k not in _INTERNAL_FIELDS
                )
            except (json.JSONDecodeError, TypeError):
                pass
        else:
            fields.update(k for k in payload if k not in _INTERNAL_FIELDS)
    return {"fields": sorted(fields)}


@app.get("/debug/stats")
async def collection_stats(field: str = "type"):
    """Returns value counts for a metadata field across all indexed nodes."""
    cache_key = f"debug_stats:{field}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

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
    payload = {
        "field": field,
        "total_nodes": total,
        "counts": dict(counts.most_common()),
    }
    redis_client.setex(cache_key, STATS_CACHE_TTL, json.dumps(payload))
    return payload


@app.get("/debug/stats/all")
async def collection_stats_all():
    """Returns value counts for every metadata field in a single Qdrant scan."""
    cache_key = "debug_stats:__all__"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    counts: dict[str, Counter] = defaultdict(Counter)
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
            if "_node_content" in payload:
                try:
                    metadata = json.loads(payload["_node_content"]).get("metadata", {})
                    for k, v in metadata.items():
                        if k not in _INTERNAL_FIELDS and v is not None:
                            counts[k][str(v)] += 1
                except (json.JSONDecodeError, TypeError):
                    pass
            else:
                for k, v in payload.items():
                    if k not in _INTERNAL_FIELDS and v is not None:
                        counts[k][str(v)] += 1
        if offset is None:
            break

    result_payload = {f: dict(c.most_common()) for f, c in counts.items()}
    redis_client.setex(cache_key, STATS_CACHE_TTL, json.dumps(result_payload))
    return result_payload


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
