import os
import logging
import uuid
import qdrant_client
from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    SimpleDirectoryReader,
    Settings,
    PromptTemplate,
)
from llama_index.core.ingestion import IngestionPipeline, IngestionCache
from llama_index.storage.kvstore.redis import RedisKVStore as RedisCache
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Setup logging
logger = logging.getLogger("backend.engine")

DEFAULT_SYSTEM_PROMPT = (
    "You are Klippy, an expert research assistant for King's Digital Lab. "
    "Your goal is to answer questions strictly using the provided context from ClickUp and GitHub. "
    "\n\nRules:\n"
    "1. Only use the provided context to answer the question.\n"
    "2. If the context does not contain enough information to answer the question, clearly state: "
    "'I am sorry, but I do not have enough information in my current index to answer that question.'\n"
    "3. Do not use any external knowledge or make up information.\n"
    "4. When possible, mention whether the information came from ClickUp or GitHub based on the metadata.\n"
    "5. Be concise and professional."
)

class KlippyEngine:
    def __init__(self, qdrant_host: str, data_dir: str, collection_name: str = "klippy_data"):
        self.qdrant_host = qdrant_host
        self.data_dir = data_dir
        self.collection_name = collection_name
        self.prompt_file = "/app/data/final/prompt.md"
        
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

    def _get_system_prompt(self) -> str:
        """Loads system prompt from file, fallback to default."""
        if os.path.exists(self.prompt_file):
            try:
                with open(self.prompt_file, "r") as f:
                    return f.read().strip()
            except Exception as e:
                logger.error(f"Failed to read prompt file {self.prompt_file}: {e}")
        return DEFAULT_SYSTEM_PROMPT
def ingest_data(self, limit: int = None):
    """Loads markdown files and indexes them. If limit is set, samples a random subset."""
    if not os.path.exists(self.data_dir):
        logger.warning(f"Data directory {self.data_dir} does not exist.")
        return

    logger.info(f"Scanning directory {self.data_dir} for markdown files...")

    reader = SimpleDirectoryReader(
        input_dir=self.data_dir,
        recursive=True,
        required_exts=[".md"]
    )

    documents = reader.load_data(show_progress=True)

    if not documents:
        logger.info("No documents found for ingestion.")
        return

    # Handle random sampling if limit is set
    if limit and limit < len(documents):
        import random
        logger.info(f"Limiting ingestion to {limit} random documents out of {len(documents)}...")
        documents = random.sample(documents, limit)

    # Ensure documents have deterministic UUIDs based on file path for Qdrant compatibility
...
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
        """Returns a query engine with a strict system prompt."""
        if self._index is None:
            # Try to load existing index from Qdrant
            self._index = VectorStoreIndex.from_vector_store(
                vector_store=self.vector_store,
                storage_context=self.storage_context
            )
            
        engine = self._index.as_query_engine(
            similarity_top_k=5,
            response_mode="compact",
            llm=Settings.llm
        )

        # Apply prompt from file
        system_prompt = self._get_system_prompt()
        template = system_prompt + "\n\nContext:\n{context_str}\n\nQuestion: {query_str}\n\nAnswer:"
        engine.update_prompts(
            {"response_synthesizer:text_qa_template": PromptTemplate(template)}
        )
        
        return engine

    def query(self, text: str) -> str:
        """Executes a query and returns the LLM-synthesized response."""
        engine = self.get_query_engine()
        response = engine.query(text)
        return str(response)
