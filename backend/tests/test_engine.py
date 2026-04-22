import pytest
from engine import KlippyEngine
from llama_index.core.vector_stores.types import MetadataFilters
from llama_index.core.base.llms.types import ChatMessage, MessageRole


@pytest.fixture
def engine(mocker):
    mocker.patch("qdrant_client.QdrantClient")
    mocker.patch("engine.IngestionCache")
    mocker.patch("engine.RedisCache")
    return KlippyEngine(qdrant_host="localhost", data_dir="/tmp/data", collection_name="test_collection")


@pytest.fixture
def engine_with_index(engine, mocker):
    mock_index = mocker.MagicMock()
    mocker.patch("llama_index.core.VectorStoreIndex.from_vector_store", return_value=mock_index)
    engine._index = mock_index
    return engine, mock_index


def test_engine_initialization(engine):
    assert engine.qdrant_host == "localhost"
    assert engine.collection_name == "test_collection"


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
