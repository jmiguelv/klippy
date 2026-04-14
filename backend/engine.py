import os
import logging
import uuid
import qdrant_client
from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    SimpleDirectoryReader,
    Settings,
)
from llama_index.core.ingestion import IngestionPipeline, IngestionCache
from llama_index.storage.kvstore.redis import RedisKVStore as RedisCache
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Setup logging
logger = logging.getLogger("backend.engine")

class KlippyEngine:
    def __init__(self, qdrant_host: str, data_dir: str, collection_name: str = "klippy_data"):
        self.qdrant_host = qdrant_host
        self.data_dir = data_dir
        self.collection_name = collection_name
        
        # Configure LlamaIndex settings
        llm_api_key = os.getenv("LLM_API_KEY")
        llm_base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        llm_model = os.getenv("LLM_MODEL", "gpt-4-turbo-preview")
        embed_model = os.getenv("EMBED_MODEL", "text-embedding-3-small")
        
        Settings.llm = OpenAI(
            model_name=llm_model, 
            api_base=llm_base_url,
            api_key=llm_api_key
        )
        
        # Determine embedding model (OpenAI vs HuggingFace)
        if embed_model.startswith("local:") or "/" in embed_model:
            model_name = embed_model.replace("local:", "")
            embed_device = os.getenv("EMBED_DEVICE", "cpu")
            logger.info(f"Using local HuggingFace embedding model: {model_name} on device: {embed_device}")
            Settings.embed_model = HuggingFaceEmbedding(
                model_name=model_name,
                device=embed_device
            )
        else:
            if "arc:lite" in embed_model.lower():
                logger.warning("WARNING: 'arc:lite' detected as EMBED_MODEL. This is typically a chat model and will likely fail for embeddings.")
            
            logger.info(f"Using OpenAI-compatible embedding model: {embed_model}")
            Settings.embed_model = OpenAIEmbedding(
                model_name=embed_model, 
                api_base=llm_base_url,
                api_key=llm_api_key
            )
        
        # Initialize Qdrant Client
        self.client = qdrant_client.QdrantClient(host=self.qdrant_host, port=6333)
        self.vector_store = QdrantVectorStore(
            client=self.client, collection_name=self.collection_name
        )
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        
        # Initialize Redis Cache for Ingestion
        self.redis_host = os.getenv("REDIS_HOST", "redis")
        self.ingest_cache = IngestionCache(
            cache=RedisCache.from_host_and_port(host=self.redis_host, port=6379),
            collection=f"ingest_cache_{self.collection_name}"
        )

        # Internal state for the index
        self._index = None

    def ingest_data(self):
        """Loads markdown files and indexes them using a cached pipeline with manual batching."""
        if not os.path.exists(self.data_dir):
            logger.warning(f"Data directory {self.data_dir} does not exist.")
            return

        logger.info(f"Scanning directory {self.data_dir} for markdown files...")
        
        reader = SimpleDirectoryReader(
            input_dir=self.data_dir,
            recursive=True,
            required_exts=[".md"]
        )
        
        # Load documents normally
        documents = reader.load_data(show_progress=True)

        if not documents:
            logger.info("No documents found for ingestion.")
            return

        # Ensure documents have deterministic UUIDs based on file path for Qdrant compatibility
        for doc in documents:
            file_path = doc.metadata.get("file_path", "")
            if file_path:
                doc.id_ = str(uuid.uuid5(uuid.NAMESPACE_URL, file_path))

        logger.info(f"Loaded {len(documents)} documents. Starting transformation pipeline...")

        pipeline = IngestionPipeline(
            transformations=[
                Settings.embed_model,
            ],
            vector_store=self.vector_store,
            cache=self.ingest_cache,
        )

        # Process in manual batches to avoid pickling errors and manage memory
        batch_size = 100
        all_nodes = []
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1} ({len(batch)} docs)...")
            nodes = pipeline.run(documents=batch, show_progress=False)
            all_nodes.extend(nodes)
        
        # Create or update index from the vector store
        self._index = VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store,
            storage_context=self.storage_context
        )
        
        logger.info(f"Ingestion complete. Total nodes processed: {len(all_nodes)}.")

    def get_query_engine(self):
        """Returns a query engine based on the current index."""
        if self._index is None:
            # Try to load existing index from Qdrant
            self._index = VectorStoreIndex.from_vector_store(
                vector_store=self.vector_store,
                storage_context=self.storage_context
            )
            
        return self._index.as_query_engine(
            similarity_top_k=5,
            response_mode="compact" # Good for synthesizing across multiple chunks
        )

    def query(self, text: str) -> str:
        """Executes a query and returns the LLM-synthesized response."""
        engine = self.get_query_engine()
        response = engine.query(text)
        return str(response)
