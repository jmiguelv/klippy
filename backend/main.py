import os
import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import redis
from contextlib import asynccontextmanager

from engine import KlippyEngine
import phoenix as px
from llama_index.core import set_global_handler

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend.main")

# Arize Phoenix Observability
px.launch_app()
set_global_handler("arize_phoenix")

class QueryRequest(BaseModel):
    text: str

class QueryResponse(BaseModel):
    answer: str
    cached: bool = False

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
    data_dir=os.getenv("DATA_DIR", "./data")
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initial data ingestion
    logger.info("Initializing engine with current data...")
    engine.ingest_data()
    yield

app = FastAPI(lifespan=lifespan, title="Klippy Backend API")

@app.post("/query", response_model=QueryResponse)
async def query_klippy(request: QueryRequest):
    # Check cache
    cache_key = f"query:{request.text}"
    cached_answer = redis_client.get(cache_key)
    if cached_answer:
        logger.info(f"Cache hit for query: {request.text}")
        return QueryResponse(answer=cached_answer, cached=True)

    try:
        answer = engine.query(request.text)
        # Store in cache (expire in 1 hour)
        redis_client.setex(cache_key, 3600, str(answer))
        return QueryResponse(answer=str(answer), cached=False)
    except Exception as e:
        logger.error(f"Error during query processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest")
async def trigger_ingestion(background_tasks: BackgroundTasks):
    """Triggers an incremental ingestion of the data directory."""
    background_tasks.add_task(engine.ingest_data)
    return {"status": "Ingestion task started in background"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
