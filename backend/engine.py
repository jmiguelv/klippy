import os
import re
import logging
import random
import uuid
import yaml
import torch
import time
import qdrant_client
from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    SimpleDirectoryReader,
    Settings,
)
from llama_index.core.ingestion import IngestionPipeline, IngestionCache
from llama_index.core.node_parser import MarkdownNodeParser
from llama_index.core.extractors import QuestionsAnsweredExtractor, KeywordExtractor
from llama_index.core.vector_stores.types import MetadataFilter, MetadataFilters
from llama_index.core.postprocessor import SimilarityPostprocessor
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


def parse_frontmatter(text: str) -> tuple[str, dict[str, str]]:
    """Strips YAML frontmatter and returns (content, metadata)."""
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not fm_match:
        return text, {}
    
    try:
        fm_data = yaml.safe_load(fm_match.group(1))
        if isinstance(fm_data, dict):
            metadata = {k: str(v) for k, v in fm_data.items() if v is not None}
            return text[fm_match.end() :], metadata
    except yaml.YAMLError as e:
        logger.warning(f"YAML parse error: {e}")
    
    return text, {}


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
        self.llm_model = llm_model
        llm_context_window = int(os.getenv("LLM_CONTEXT_WINDOW", "3900"))
        embed_model = os.getenv("EMBED_MODEL") or "text-embedding-3-small"

        # Use OpenAILike for OpenAI-compatible endpoints
        Settings.llm = OpenAILike(
            model=llm_model,
            api_base=llm_base_url,
            api_key=llm_api_key,
            is_chat_model=True,
            temperature=0.1,
            context_window=llm_context_window,
        )
        Settings.context_window = llm_context_window

        if embed_model.startswith("local:") or "/" in embed_model:
            model_name = embed_model.replace("local:", "")
            env_device = os.getenv("EMBED_DEVICE")
            if env_device:
                embed_device = env_device
                logger.info(f"Embed device set via EMBED_DEVICE env var: {embed_device}")
            elif torch.accelerator.is_available():
                embed_device = torch.accelerator.current_accelerator().type
                logger.info(f"Embed device autodetected: {embed_device}")
            else:
                embed_device = "cpu"
                logger.info("No accelerator available, embed device defaulting to: cpu")
            if embed_device == "mps":
                torch.set_default_dtype(torch.float32)
            logger.info(
                f"Using local HuggingFace embedding model: {model_name} on device: {embed_device}"
            )
            Settings.embed_model = HuggingFaceEmbedding(
                model_name=model_name,
                device=embed_device,
                trust_remote_code=True,
                model_kwargs={"default_task": "retrieval"},
            )
        else:
            logger.info(f"Using OpenAI-compatible embedding model: {embed_model}")
            Settings.embed_model = OpenAIEmbedding(
                model_name=embed_model, api_base=llm_base_url, api_key=llm_api_key
            )

        # Initialize Qdrant Client
        self.client = qdrant_client.QdrantClient(host=self.qdrant_host, port=6333)
        self.aclient = qdrant_client.AsyncQdrantClient(host=self.qdrant_host, port=6333)
        self.vector_store = QdrantVectorStore(
            client=self.client, aclient=self.aclient, collection_name=self.collection_name, dense_vector_name="text-dense"
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

    def ingest_data(
        self,
        limit: int | None = None,
        force: bool = False,
        extract_questions: bool = False,
        extract_keywords: bool = False,
    ) -> None:
        """Loads markdown files and indexes them. If limit is set, samples a random subset. If force is True, ignores cache."""
        if not os.path.exists(self.data_dir):
            logger.warning(f"Data directory {self.data_dir} does not exist.")
            return

        if force:
            logger.info("Force re-index: deleting existing collection...")
            self.client.delete_collection(self.collection_name)
            self.vector_store = QdrantVectorStore(
                client=self.client,
                aclient=self.aclient,
                collection_name=self.collection_name,
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

            content, metadata = parse_frontmatter(doc.text or "")
            doc.metadata.update(metadata)
            doc.set_content(content)

        logger.info(
            f"Loaded {len(documents)} documents. Starting transformation pipeline..."
        )

        transformations: list = [MarkdownNodeParser(include_metadata=True)]
        if extract_questions or extract_keywords:
            if extract_questions:
                logger.info("Enabling QuestionsAnsweredExtractor...")
                transformations.append(
                    QuestionsAnsweredExtractor(llm=Settings.llm, num_questions=3)
                )
            if extract_keywords:
                logger.info("Enabling KeywordExtractor...")
                transformations.append(KeywordExtractor(llm=Settings.llm, keywords=5))

        transformations.append(Settings.embed_model)

        pipeline = IngestionPipeline(
            transformations=transformations,
            vector_store=self.vector_store,
            cache=self.ingest_cache if not force else None,
        )

        # Process in manual batches to avoid pickling errors and manage memory
        batch_size = 20 if (extract_questions or extract_keywords) else 100
        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            logger.info(
                f"Processing batch {i // batch_size + 1}/{(len(documents) - 1) // batch_size + 1} ({len(batch)} docs)..."
            )
            try:
                pipeline.run(documents=batch, show_progress=False)
            except Exception as e:
                if extract_questions or extract_keywords:
                    logger.warning(
                        f"Metadata extraction failed for batch (likely LLM error: {e}). "
                        "Retrying batch without extractions..."
                    )
                    # Fallback pipeline without extractors
                    fallback_pipeline = IngestionPipeline(
                        transformations=[
                            MarkdownNodeParser(include_metadata=True),
                            Settings.embed_model,
                        ],
                        vector_store=self.vector_store,
                        cache=self.ingest_cache if not force else None,
                    )
                    try:
                        fallback_pipeline.run(documents=batch, show_progress=False)
                    except Exception as fallback_e:
                        logger.error(f"Ingestion failed even without extraction: {fallback_e}")
                        raise fallback_e
                else:
                    logger.error(f"Ingestion failed for batch: {e}")
                    raise e

        # Create or update index from the vector store
        self._index = VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store,
            storage_context=self.storage_context,
            embed_model=Settings.embed_model,
        )

        logger.info("Ingestion complete.")

    def get_chat_engine(
        self,
        chat_history=None,
        filters: dict[str, str] | None = None,
        top_k: int = 10,
        similarity_cutoff: float | None = None,
    ):
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

        node_postprocessors = []
        if similarity_cutoff is not None and similarity_cutoff > 0.0:
            node_postprocessors.append(
                SimilarityPostprocessor(similarity_cutoff=similarity_cutoff)
            )

        return self._index.as_chat_engine(
            chat_mode="condense_plus_context",
            chat_history=chat_history or [],
            context_prompt=context_prompt,
            similarity_top_k=top_k,
            node_postprocessors=node_postprocessors,
            llm=Settings.llm,
            filters=metadata_filters,
        )

    def chat(
        self,
        message: str,
        chat_history=None,
        filters: dict[str, str] | None = None,
        top_k: int = 10,
        similarity_cutoff: float | None = None,
    ):
        """Executes a chat turn and returns the response object with timings."""

        engine = self.get_chat_engine(
            chat_history=chat_history,
            filters=filters,
            top_k=top_k,
            similarity_cutoff=similarity_cutoff,
        )

        start_time = time.time()
        response = engine.chat(message)
        total_time_ms = int((time.time() - start_time) * 1000)

        if response.metadata is None:
            response.metadata = {}
        response.metadata["total_time_ms"] = total_time_ms
        return response

    def stream_chat(
        self,
        message: str,
        chat_history=None,
        filters: dict[str, str] | None = None,
        top_k: int = 10,
        similarity_cutoff: float | None = None,
    ):
        """Returns a streaming chat response for use with SSE endpoints."""
        engine = self.get_chat_engine(
            chat_history=chat_history,
            filters=filters,
            top_k=top_k,
            similarity_cutoff=similarity_cutoff,
        )
        return engine.stream_chat(message)

    async def astream_chat(
        self,
        message: str,
        chat_history=None,
        filters: dict[str, str] | None = None,
        top_k: int = 10,
        similarity_cutoff: float | None = None,
    ):
        """Returns an asynchronous streaming chat response."""
        engine = self.get_chat_engine(
            chat_history=chat_history,
            filters=filters,
            top_k=top_k,
            similarity_cutoff=similarity_cutoff,
        )
        return await engine.astream_chat(message)
