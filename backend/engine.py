import os
import re
import logging
import random
import uuid
import yaml
import qdrant_client
from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    SimpleDirectoryReader,
    Settings,
)
from llama_index.core.ingestion import IngestionPipeline, IngestionCache
from llama_index.core.node_parser import MarkdownNodeParser
from llama_index.core.vector_stores.types import MetadataFilter, MetadataFilters
from llama_index.storage.kvstore.redis import RedisKVStore as RedisCache
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.llms.openai_like import OpenAILike
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
    def __init__(
        self, qdrant_host: str, data_dir: str, collection_name: str = "klippy_data"
    ):
        self.qdrant_host = qdrant_host
        self.data_dir = data_dir
        self.collection_name = collection_name
        self.prompt_file = "/app/config/prompt.md"

        # Configure LlamaIndex settings
        llm_api_key = os.getenv("LLM_API_KEY")
        llm_base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        llm_model = os.getenv("LLM_MODEL", "gpt-4-turbo-preview")
        embed_model = os.getenv("EMBED_MODEL", "text-embedding-3-small")

        # Use OpenAILike for OpenAI-compatible endpoints
        Settings.llm = OpenAILike(
            model=llm_model,
            api_base=llm_base_url,
            api_key=llm_api_key,
            is_chat_model=True,
            temperature=0.1,
        )

        if embed_model.startswith("local:") or "/" in embed_model:
            model_name = embed_model.replace("local:", "")
            embed_device = os.getenv("EMBED_DEVICE", "cpu")
            logger.info(
                f"Using local HuggingFace embedding model: {model_name} on device: {embed_device}"
            )
            Settings.embed_model = HuggingFaceEmbedding(
                model_name=model_name, device=embed_device, trust_remote_code=True
            )
        else:
            logger.info(f"Using OpenAI-compatible embedding model: {embed_model}")
            Settings.embed_model = OpenAIEmbedding(
                model_name=embed_model, api_base=llm_base_url, api_key=llm_api_key
            )

        # Initialize Qdrant Client
        self.client = qdrant_client.QdrantClient(host=self.qdrant_host, port=6333)
        self.vector_store = QdrantVectorStore(
            client=self.client, collection_name=self.collection_name
        )
        self.storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store
        )

        # Initialize Redis Cache for Ingestion
        self.redis_host = os.getenv("REDIS_HOST", "redis")
        self.ingest_cache = IngestionCache(
            cache=RedisCache.from_host_and_port(host=self.redis_host, port=6379),
            collection=f"ingest_cache_{self.collection_name}",
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

    def ingest_data(self, limit: int = None, force: bool = False):
        """Loads markdown files and indexes them. If limit is set, samples a random subset. If force is True, ignores cache."""
        if not os.path.exists(self.data_dir):
            logger.warning(f"Data directory {self.data_dir} does not exist.")
            return

        if force:
            logger.info("Force re-index: deleting existing collection...")
            self.client.delete_collection(self.collection_name)
            self.vector_store = QdrantVectorStore(
                client=self.client, collection_name=self.collection_name
            )
            self.storage_context = StorageContext.from_defaults(
                vector_store=self.vector_store
            )
            self._index = None

        logger.info(f"Scanning directory {self.data_dir} for markdown files...")

        reader = SimpleDirectoryReader(
            input_dir=self.data_dir, recursive=True, required_exts=[".md"]
        )

        documents = reader.load_data(show_progress=True)

        if not documents:
            logger.info("No documents found for ingestion.")
            return

        if limit and limit < len(documents):
            logger.info(
                f"Limiting ingestion to {limit} random documents out of {len(documents)}..."
            )
            documents = random.sample(documents, limit)

        for doc in documents:
            file_path = doc.metadata.get("file_path", "")
            if file_path:
                doc.id_ = str(uuid.uuid5(uuid.NAMESPACE_URL, file_path))

            # Strip YAML frontmatter from content and extract fields as metadata
            text = doc.text or ""
            fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
            if fm_match:
                try:
                    fm_data = yaml.safe_load(fm_match.group(1))
                    if isinstance(fm_data, dict):
                        for k, v in fm_data.items():
                            if v is not None:
                                doc.metadata[k] = str(v)
                except yaml.YAMLError as e:
                    logger.warning(f"YAML parse error in {file_path}: {e}")
                # Remove frontmatter from the text so it isn't indexed as content
                doc.set_content(text[fm_match.end() :])

        logger.info(
            f"Loaded {len(documents)} documents. Starting transformation pipeline..."
        )

        pipeline = IngestionPipeline(
            transformations=[
                MarkdownNodeParser(include_metadata=True),
                Settings.embed_model,
            ],
            vector_store=self.vector_store,
            cache=self.ingest_cache if not force else None,
        )

        # Process in manual batches to avoid pickling errors and manage memory
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            logger.info(
                f"Processing batch {i // batch_size + 1}/{(len(documents) - 1) // batch_size + 1} ({len(batch)} docs)..."
            )
            pipeline.run(documents=batch, show_progress=False)

        # Create or update index from the vector store
        self._index = VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store,
            storage_context=self.storage_context,
            embed_model=Settings.embed_model,
        )

        logger.info("Ingestion complete.")

    def get_chat_engine(self, chat_history=None, filters: dict[str, str] | None = None):
        """Returns a chat engine with conversational memory."""
        if self._index is None:
            self._index = VectorStoreIndex.from_vector_store(
                vector_store=self.vector_store,
                storage_context=self.storage_context,
                embed_model=Settings.embed_model,
            )

        system_prompt = self._get_system_prompt()

        # Format the context prompt correctly for condense_plus_context
        # This acts as the system prompt and is where context is injected
        context_prompt = (
            system_prompt + "\n\n"
            "Here are the relevant documents for the context:\n"
            "{context_str}\n"
            "\nInstruction: Use the previous chat history, or the context above, to interact and help the user."
        )

        metadata_filters = (
            MetadataFilters(
                filters=[MetadataFilter(key=k, value=v) for k, v in filters.items()]
            )
            if filters
            else None
        )

        return self._index.as_chat_engine(
            chat_mode="condense_plus_context",
            chat_history=chat_history or [],
            context_prompt=context_prompt,
            similarity_top_k=10,
            llm=Settings.llm,
            filters=metadata_filters,
        )

    def chat(
        self, message: str, chat_history=None, filters: dict[str, str] | None = None
    ):
        """Executes a chat turn and returns the response object with timings."""
        import time

        engine = self.get_chat_engine(chat_history=chat_history, filters=filters)

        start_time = time.time()
        response = engine.chat(message)
        total_time_ms = int((time.time() - start_time) * 1000)

        # Add timings and history to metadata
        if response.metadata is None:
            response.metadata = {}
        response.metadata["total_time_ms"] = total_time_ms
        response.metadata["chat_history"] = [m.dict() for m in engine.chat_history]

        return response
