import os
import logging
import argparse
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis
import json
from contextlib import asynccontextmanager

from engine import KlippyEngine
from llama_index.core import set_global_handler

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

class QueryResponse(BaseModel):
    answer: str
    cached: bool = False
    sources: list[dict] = []

class IngestRequest(BaseModel):
    limit: int = None

# Redis for Caching
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)

# Engine initialization
engine = KlippyEngine(
    qdrant_host=os.getenv("QDRANT_HOST", "localhost"),
    data_dir=os.getenv("DATA_DIR", "/app/data/raw")
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # No longer running initial ingestion on startup
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

@app.post("/query", response_model=QueryResponse)
async def query_klippy(request: QueryRequest):
    cache_key = f"query:{request.text}"
    try:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            logger.info(f"Cache hit for query: {request.text}")
            parsed = json.loads(cached_data)
            return QueryResponse(answer=parsed["answer"], cached=True, sources=parsed.get("sources", []))
    except Exception as e:
        logger.warning(f"Redis cache error: {e}")

    try:
        # Update engine to return full response object
        response_obj = engine.query_detailed(request.text)
        answer = str(response_obj)
        
        # Extract sources
        sources = []
        for node in response_obj.source_nodes:
            metadata = node.node.metadata
            sources.append({
                "source": metadata.get("source"),
                "type": metadata.get("type"),
                "id": metadata.get("id"),
                "url": metadata.get("url"),
                "title": metadata.get("file_name", "Untitled"),
                "score": float(node.score) if node.score is not None else 0.0
            })

        # Cache the detailed result
        try:
            cache_val = json.dumps({"answer": answer, "sources": sources})
            redis_client.setex(cache_key, 3600, cache_val)
        except Exception as e:
            logger.warning(f"Failed to write to Redis: {e}")
            
        return QueryResponse(answer=answer, cached=False, sources=sources)
    except Exception as e:
        logger.error(f"Error during query processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest")
async def trigger_ingestion(request: IngestRequest, background_tasks: BackgroundTasks):
    """Triggers a manual ingestion. Can optionally limit number of docs."""
    background_tasks.add_task(engine.ingest_data, limit=request.limit)
    return {"status": "Ingestion task started in background", "limit": request.limit}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

def main():
    parser = argparse.ArgumentParser(description="Klippy Backend and Indexer")
    parser.add_argument("--ingest", action="store_true", help="Run indexing and exit")
    parser.add_argument("--limit", type=int, help="Limit number of documents to ingest (random sampling)")
    parser.add_argument("--serve", action="store_true", default=True, help="Run FastAPI server (default)")
    
    args, unknown = parser.parse_known_args()

    if args.ingest:
        logger.info(f"CLI: Starting manual ingestion (limit={args.limit})...")
        engine.ingest_data(limit=args.limit)
        logger.info("CLI: Ingestion complete. Exiting.")
    else:
        import uvicorn
        logger.info("CLI: Starting FastAPI server...")
        uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
