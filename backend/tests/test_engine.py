import pytest
from engine import KlippyEngine
from llama_index.core.vector_stores.types import MetadataFilters
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.llms import LLM, LLMMetadata


@pytest.fixture
def engine(mocker):
    mocker.patch("qdrant_client.QdrantClient")
    mocker.patch("qdrant_client.AsyncQdrantClient")
    mocker.patch("engine.IngestionCache")
    mocker.patch("engine.RedisCache")
    
    # Mock delete_nodes on the class level to avoid Pydantic attribute errors
    mocker.patch("engine.QdrantVectorStore.delete_nodes")
    
    # Mock OpenAILike so it passes isinstance(..., LLM)
    mock_llm = mocker.Mock(spec=LLM)
    mock_llm.callback_manager = None
    mock_llm.metadata = LLMMetadata(context_window=3900, num_output=256)
    mock_llm.completion_to_prompt = mocker.Mock()
    mock_llm.messages_to_prompt = mocker.Mock()
    mocker.patch("engine.OpenAILike", return_value=mock_llm)
    
    # Mock HuggingFaceEmbedding so it passes isinstance(..., BaseEmbedding)
    mock_embed = mocker.Mock(spec=BaseEmbedding)
    mocker.patch("engine.HuggingFaceEmbedding", return_value=mock_embed)
    
    return KlippyEngine(qdrant_host="localhost", data_dir="/tmp/data", collection_name="test_collection")


@pytest.fixture
def engine_with_index(engine, mocker):
    mock_index = mocker.MagicMock()
    mocker.patch("llama_index.core.VectorStoreIndex.from_vector_store", return_value=mock_index)
    engine._index = mock_index
    return engine, mock_index


def test_engine_initialization(engine, mocker):
    assert engine.qdrant_host == "localhost"
    assert engine.collection_name == "test_collection"


def test_context_window_config(mocker):
    mocker.patch("qdrant_client.QdrantClient")
    mocker.patch("qdrant_client.AsyncQdrantClient")
    mocker.patch("engine.IngestionCache")
    mocker.patch("engine.RedisCache")
    
    mock_llm_instance = mocker.Mock(spec=LLM)
    mock_llm_instance.callback_manager = None
    mock_llm_instance.metadata = LLMMetadata(context_window=3900, num_output=256)
    mock_llm_class = mocker.patch("engine.OpenAILike", return_value=mock_llm_instance)
    
    # Mock HuggingFaceEmbedding so it passes isinstance(..., BaseEmbedding)
    mock_embed = mocker.Mock(spec=BaseEmbedding)
    mocker.patch("engine.HuggingFaceEmbedding", return_value=mock_embed)
    mocker.patch("engine.OpenAIEmbedding", return_value=mock_embed)
    
    import os
    mocker.patch.dict(os.environ, {"LLM_CONTEXT_WINDOW": "123456"})
    
    KlippyEngine(qdrant_host="localhost", data_dir="/tmp/data", collection_name="test_collection")
    
    # Check if OpenAILike was called with the correct context_window
    _, kwargs = mock_llm_class.call_args
    assert kwargs["context_window"] == 123456
    
    from llama_index.core import Settings
    assert Settings.context_window == 123456


def test_get_chat_engine_filters(engine_with_index):
    engine, mock_index = engine_with_index
    filters = {"type": "bug", "status": "open"}

    engine.get_chat_engine(filters=filters)

    _, kwargs = mock_index.as_chat_engine.call_args
    assert isinstance(kwargs["filters"], MetadataFilters)
    assert len(kwargs["filters"].filters) == 2
    keys = [f.key for f in kwargs["filters"].filters]
    assert "type" in keys
    assert "status" in keys


def test_get_chat_engine_multiple_filters(engine_with_index):
    engine, mock_index = engine_with_index
    filters = {"type": "bug", "status": "open", "priority": "high"}

    engine.get_chat_engine(filters=filters)

    _, kwargs = mock_index.as_chat_engine.call_args
    metadata_filters = kwargs["filters"]
    assert len(metadata_filters.filters) == 3
    keys_values = {(f.key, f.value) for f in metadata_filters.filters}
    assert ("type", "bug") in keys_values
    assert ("status", "open") in keys_values
    assert ("priority", "high") in keys_values


def test_chat_passes_history_to_engine(engine_with_index, mocker):
    engine, mock_index = engine_with_index
    mock_chat_engine = mock_index.as_chat_engine.return_value
    mock_response = mocker.MagicMock()
    mock_response.metadata = {}
    mock_chat_engine.chat.return_value = mock_response
    mock_chat_engine.chat_history = []

    history = [ChatMessage(role=MessageRole.USER, content="hello")]
    response = engine.chat("how are you?", chat_history=history)

    _, kwargs = mock_index.as_chat_engine.call_args
    assert kwargs["chat_history"] == history
    assert "chat_history" not in response.metadata


def test_chat_with_filters(engine_with_index, mocker):
    engine, mock_index = engine_with_index
    mock_chat_engine = mock_index.as_chat_engine.return_value
    mock_chat_engine.chat.return_value = mocker.MagicMock()
    mock_chat_engine.chat_history = []

    engine.chat("Tell me about GitHub issues", filters={"source": "github"})

    _, kwargs = mock_index.as_chat_engine.call_args
    assert kwargs["filters"].filters[0].key == "source"
    assert kwargs["filters"].filters[0].value == "github"


def test_chat_no_filters_or_history(engine_with_index, mocker):
    engine, mock_index = engine_with_index
    mock_chat_engine = mock_index.as_chat_engine.return_value
    mock_chat_engine.chat.return_value = mocker.MagicMock()
    mock_chat_engine.chat_history = []

    engine.chat("Hello")

    _, kwargs = mock_index.as_chat_engine.call_args
    assert kwargs["filters"] is None
    assert kwargs["chat_history"] == []


def test_similarity_cutoff_respects_threshold(engine_with_index, mocker):
    engine, mock_index = engine_with_index
    from llama_index.core.postprocessor import SimilarityPostprocessor

    engine.get_chat_engine(similarity_cutoff=0.8)

    _, kwargs = mock_index.as_chat_engine.call_args
    postprocessors = kwargs["node_postprocessors"]
    assert len(postprocessors) == 1
    assert isinstance(postprocessors[0], SimilarityPostprocessor)
    assert postprocessors[0].similarity_cutoff == 0.8


@pytest.mark.asyncio
async def test_astream_chat(engine_with_index, mocker):
    engine, mock_index = engine_with_index
    mock_chat_engine = mock_index.as_chat_engine.return_value
    
    # Ensure astream_chat is an AsyncMock
    mock_chat_engine.astream_chat = mocker.AsyncMock()

    # Mock the async streaming response object
    mock_streaming_response = mocker.MagicMock()

    async def mock_async_gen():
        yield "Hello"
        yield " world"

    mock_streaming_response.async_response_gen = mock_async_gen
    mock_chat_engine.astream_chat.return_value = mock_streaming_response

    response = await engine.astream_chat("Hi")

    assert response == mock_streaming_response
    tokens = [t async for t in response.async_response_gen()]
    assert tokens == ["Hello", " world"]
    mock_chat_engine.astream_chat.assert_called_once_with("Hi")


def test_ingest_data_with_extractors(engine, mocker):
    mock_pipeline = mocker.patch("engine.IngestionPipeline")
    mock_reader = mocker.patch("engine.SimpleDirectoryReader")
    mock_reader.return_value.load_data.return_value = [mocker.Mock(text="test content", metadata={"file_path": "test.md"})]
    mocker.patch("engine.parse_frontmatter", return_value=("test content", {}))
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("llama_index.core.VectorStoreIndex.from_vector_store")

    # Test both enabled
    engine.ingest_data(extract_questions=True, extract_keywords=True)

    _, kwargs = mock_pipeline.call_args
    transformations = kwargs["transformations"]
    
    from llama_index.core.extractors import QuestionsAnsweredExtractor, KeywordExtractor
    from llama_index.core.node_parser import MarkdownNodeParser
    
    assert any(isinstance(t, MarkdownNodeParser) for t in transformations)
    assert any(isinstance(t, QuestionsAnsweredExtractor) for t in transformations)
    assert any(isinstance(t, KeywordExtractor) for t in transformations)

def test_ingest_data_with_independent_extractors(engine, mocker):
    mock_pipeline = mocker.patch("engine.IngestionPipeline")
    mock_reader = mocker.patch("engine.SimpleDirectoryReader")
    mock_reader.return_value.load_data.return_value = [mocker.Mock(text="test content", metadata={"file_path": "test.md"})]
    mocker.patch("engine.parse_frontmatter", return_value=("test content", {}))
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("llama_index.core.VectorStoreIndex.from_vector_store")

    from llama_index.core.extractors import QuestionsAnsweredExtractor, KeywordExtractor

    # Test only keywords
    engine.ingest_data(extract_keywords=True)
    _, kwargs = mock_pipeline.call_args
    transformations = kwargs["transformations"]
    assert any(isinstance(t, KeywordExtractor) for t in transformations)
    assert not any(isinstance(t, QuestionsAnsweredExtractor) for t in transformations)

    # Test only questions
    engine.ingest_data(extract_questions=True)
    _, kwargs = mock_pipeline.call_args
    transformations = kwargs["transformations"]
    assert any(isinstance(t, QuestionsAnsweredExtractor) for t in transformations)
    assert not any(isinstance(t, KeywordExtractor) for t in transformations)

def test_ingest_data_fallback_on_extractor_failure(engine, mocker):
    # Setup: 1st pipeline.run fails, 2nd (fallback) succeeds
    mock_pipeline = mocker.patch("engine.IngestionPipeline")
    mock_pipeline.return_value.run.side_effect = [Exception("LLM Error"), None]
    
    mock_reader = mocker.patch("engine.SimpleDirectoryReader")
    mock_reader.return_value.load_data.return_value = [mocker.Mock(text="test content", metadata={"file_path": "test.md"})]
    mocker.patch("engine.parse_frontmatter", return_value=("test content", {}))
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("llama_index.core.VectorStoreIndex.from_vector_store")

    # This should not raise an exception
    engine.ingest_data(extract_keywords=True)
    
    # Verify it was called twice (once for initial fail, once for fallback)
    assert mock_pipeline.return_value.run.call_count == 2
    
    # Verify fallback transformations (2nd call)
    _, fallback_kwargs = mock_pipeline.call_args
    fallback_transformations = fallback_kwargs["transformations"]
    from llama_index.core.extractors import QuestionsAnsweredExtractor, KeywordExtractor
    assert not any(isinstance(t, QuestionsAnsweredExtractor) for t in fallback_transformations)
    assert not any(isinstance(t, KeywordExtractor) for t in fallback_transformations)

def test_ingest_data_replaces_existing_docs(engine, mocker):
    mocker.patch("engine.IngestionPipeline")
    mock_reader = mocker.patch("engine.SimpleDirectoryReader")
    
    # Mock document with a specific ID
    mock_doc = mocker.Mock(text="test content")
    mock_doc.id_ = "existing-doc-id"
    mock_doc.metadata = {"file_path": "test.md"}
    mock_reader.return_value.load_data.return_value = [mock_doc]
    
    mocker.patch("engine.parse_frontmatter", return_value=("test content", {}))
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("llama_index.core.VectorStoreIndex.from_vector_store")

    engine.ingest_data()

    # Verify delete_nodes was called with the document ID (UUID5 of "test.md")
    expected_id = "7444c9da-e923-571f-92e6-37b5ba0c2fa2"
    engine.vector_store.delete_nodes.assert_called_once_with(node_ids=[expected_id])
