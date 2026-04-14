from engine import KlippyEngine

def test_engine_initialization(mocker):
    # Mock QdrantClient and LlamaIndex components
    mocker.patch("qdrant_client.QdrantClient")
    mocker.patch("llama_index.core.VectorStoreIndex")
    
    engine = KlippyEngine(
        qdrant_host="localhost",
        data_dir="/tmp/data",
        collection_name="test_collection"
    )
    
    assert engine.qdrant_host == "localhost"
    assert engine.collection_name == "test_collection"
