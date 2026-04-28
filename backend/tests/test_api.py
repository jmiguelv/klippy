import pytest
from unittest.mock import patch, MagicMock

# Only mock external clients that try to connect on init
with patch("qdrant_client.QdrantClient"), \
     patch("qdrant_client.AsyncQdrantClient"), \
     patch("redis.Redis"), \
     patch("engine.IngestionCache"), \
     patch("engine.RedisCache"):
    from main import app, engine, redis_client, _extract_payload_field, _aggregate_corpus_stats

from fastapi.testclient import TestClient
import json

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_get_questions_empty(mocker):
    # Mock engine.client.scroll to return empty result
    mocker.patch.object(engine.client, "scroll", return_value=([], None))
    
    response = client.get("/questions?n=5")
    assert response.status_code == 200
    assert response.json() == {"questions": []}

def test_get_questions_with_data(mocker):
    # Mock point with questions metadata
    metadata_key = "questions_this_excerpt_can_answer"
    mock_point = MagicMock()
    # Using strict format: starts with question word, ends with ?, 
    # and using double-newlines for blocks to match implementation
    mock_point.payload = {
        metadata_key: "What is Klippy?\n\nHow to use it?"
    }
    
    mocker.patch.object(engine.client, "scroll", return_value=([mock_point], None))
    
    response = client.get("/questions?n=2")
    assert response.status_code == 200
    data = response.json()
    assert "questions" in data
    assert len(data["questions"]) == 2
    assert "What is Klippy?" in data["questions"]
    assert "How to use it?" in data["questions"]

def test_get_questions_sampling(mocker):
    metadata_key = "questions_this_excerpt_can_answer"
    mock_point = MagicMock()
    mock_point.payload = {
        metadata_key: "What Q1?\n\nHow Q2?\n\nWhere Q3?\n\nWho Q4?\n\nWhy Q5?"
    }
    
    mocker.patch.object(engine.client, "scroll", return_value=([mock_point], None))
    
    response = client.get("/questions?n=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data["questions"]) == 3
    for q in data["questions"]:
        assert q.endswith("?")

def test_get_questions_nested_metadata(mocker):
    metadata_key = "questions_this_excerpt_can_answer"
    mock_point = MagicMock()
    # No top-level metadata, only in _node_content
    mock_point.payload = {
        "_node_content": json.dumps({
            "metadata": {
                metadata_key: "What is a Nested Question?"
            }
        })
    }
    
    mocker.patch.object(engine.client, "scroll", return_value=([mock_point], None))
    
    response = client.get("/questions?n=1")
    assert response.status_code == 200
    data = response.json()
    assert data["questions"] == ["What is a Nested Question?"]

def test_get_questions_cleaning(mocker):
    metadata_key = "questions_this_excerpt_can_answer"
    mock_point = MagicMock()
    mock_point.payload = {
        metadata_key: (
            "1. What is the status?\n\n"
            "   *Answer:* Open.\n\n"
            "2. How does it work? (extra info)\n\n"
            "Not a question\n\n"
            "Question: Why use Klippy?\n\n"
        )
    }
    
    mocker.patch.object(engine.client, "scroll", return_value=([mock_point], None))
    
    response = client.get("/questions?n=10")
    assert response.status_code == 200
    questions = response.json()["questions"]
    
    assert "What is the status?" in questions
    assert "How does it work?" in questions
    assert "Why use Klippy?" in questions
    assert len(questions) == 3
    
    for q in questions:
        assert "Answer:" not in q
        assert "(" not in q
        assert q.endswith("?")


def test_get_keywords_empty(mocker):
    mocker.patch.object(engine.client, "scroll", return_value=([], None))
    response = client.get("/keywords?n=5")
    assert response.status_code == 200
    assert response.json() == {"keywords": []}


def test_get_keywords_with_data(mocker):
    metadata_key = "excerpt_keywords"
    mock_point = MagicMock()
    # Test both comma-separated string and list formats
    mock_point.payload = {
        metadata_key: "ai, machine learning, rag"
    }
    
    mock_point_2 = MagicMock()
    mock_point_2.payload = {
        metadata_key: ["search", "indexing"]
    }
    
    mocker.patch.object(engine.client, "scroll", return_value=([mock_point, mock_point_2], None))
    
    response = client.get("/keywords?n=10")
    assert response.status_code == 200
    data = response.json()
    assert "keywords" in data
    keywords = data["keywords"]
    assert "Ai" in keywords
    assert "Machine Learning" in keywords
    assert "Rag" in keywords
    assert "Search" in keywords
    assert "Indexing" in keywords
    assert len(keywords) == 5

# ── _extract_payload_field ────────────────────────────────────────────────────

def test_extract_payload_field_top_level():
    assert _extract_payload_field({"source": "GitHub"}, "source") == "GitHub"

def test_extract_payload_field_node_content():
    payload = {"_node_content": json.dumps({"metadata": {"source": "ClickUp"}})}
    assert _extract_payload_field(payload, "source") == "ClickUp"

def test_extract_payload_field_top_level_takes_precedence():
    payload = {
        "source": "TopLevel",
        "_node_content": json.dumps({"metadata": {"source": "Nested"}}),
    }
    assert _extract_payload_field(payload, "source") == "TopLevel"

def test_extract_payload_field_missing_returns_none():
    assert _extract_payload_field({}, "source") is None
    assert _extract_payload_field({"_node_content": json.dumps({"metadata": {}})}, "source") is None

def test_extract_payload_field_invalid_json_returns_none():
    assert _extract_payload_field({"_node_content": "not-json"}, "source") is None


# ── _aggregate_corpus_stats ───────────────────────────────────────────────────

def test_aggregate_corpus_stats_empty():
    result = _aggregate_corpus_stats([])
    assert result["overview"]["total_nodes"] == 0
    assert result["overview"]["sources"] == []
    assert result["overview"]["last_ingested"] is None
    assert result["overview"]["date_range"] == {"from": None, "to": None}
    assert result["keywords"]["top"] == []
    assert result["by_source"] == {}
    assert result["by_type"] == {}


def _make_point(payload: dict):
    pt = MagicMock()
    pt.payload = payload
    return pt


def test_aggregate_corpus_stats_keyword_counting_string():
    pt = _make_point({
        "excerpt_keywords": "ai, machine learning, ai",
        "source": "GitHub",
        "type": "readme",
        "last_modified_date": "2026-01-01",
    })
    result = _aggregate_corpus_stats([pt])
    kw_map = {kw["keyword"]: kw["count"] for kw in result["keywords"]["top"]}
    assert kw_map["Ai"] == 2
    assert kw_map["Machine Learning"] == 1


def test_aggregate_corpus_stats_keyword_counting_list():
    pt = _make_point({
        "excerpt_keywords": ["rag", "llm", "rag"],
        "source": "GitHub",
    })
    result = _aggregate_corpus_stats([pt])
    kw_map = {kw["keyword"]: kw["count"] for kw in result["keywords"]["top"]}
    assert kw_map["Rag"] == 2
    assert kw_map["Llm"] == 1


def test_aggregate_corpus_stats_source_and_type_breakdown():
    pts = [
        _make_point({"source": "ClickUp", "type": "task", "last_modified_date": "2026-01-01", "excerpt_keywords": ""}),
        _make_point({"source": "GitHub",  "type": "readme", "last_modified_date": "2026-02-01", "excerpt_keywords": ""}),
        _make_point({"source": "ClickUp", "type": "doc", "last_modified_date": "2026-03-01", "excerpt_keywords": ""}),
    ]
    result = _aggregate_corpus_stats(pts)
    assert result["overview"]["total_nodes"] == 3
    assert result["by_source"]["ClickUp"]["nodes"] == 2
    assert result["by_source"]["GitHub"]["nodes"] == 1
    assert result["by_type"]["task"] == 1
    assert result["by_type"]["readme"] == 1
    assert result["by_type"]["doc"] == 1
    assert result["overview"]["date_range"]["from"] == "2026-01-01"
    assert result["overview"]["date_range"]["to"] == "2026-03-01"
    assert result["overview"]["last_ingested"] == "2026-03-01"


def test_aggregate_corpus_stats_top_30_keywords_global():
    kws = ", ".join(f"kw{i}" for i in range(35))
    pt = _make_point({"excerpt_keywords": kws, "source": "X"})
    result = _aggregate_corpus_stats([pt])
    assert len(result["keywords"]["top"]) == 30


def test_aggregate_corpus_stats_top_5_keywords_per_source():
    kws = ", ".join(f"kw{i}" for i in range(10))
    pt = _make_point({"excerpt_keywords": kws, "source": "GitHub"})
    result = _aggregate_corpus_stats([pt])
    assert len(result["by_source"]["GitHub"]["top_keywords"]) == 5


def test_aggregate_corpus_stats_keyword_title_case():
    pt = _make_point({"excerpt_keywords": "machine learning", "source": "X"})
    result = _aggregate_corpus_stats([pt])
    assert result["keywords"]["top"][0]["keyword"] == "Machine Learning"
    assert result["by_source"]["X"]["top_keywords"] == ["Machine Learning"]

# ── GET /corpus/stats ─────────────────────────────────────────────────────────

def test_get_corpus_stats_empty_collection(mocker):
    mocker.patch.object(engine.client, "scroll", return_value=([], None))
    mocker.patch.object(redis_client, "get", return_value=None)
    mocker.patch.object(redis_client, "setex")

    response = client.get("/corpus/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["overview"]["total_nodes"] == 0
    assert data["keywords"]["top"] == []
    assert data["by_source"] == {}
    assert data["by_type"] == {}


def test_get_corpus_stats_with_data(mocker):
    pt = MagicMock()
    pt.payload = {
        "excerpt_keywords": "rag, llm",
        "source": "GitHub",
        "type": "readme",
        "last_modified_date": "2026-01-15",
    }
    mocker.patch.object(engine.client, "scroll", return_value=([pt], None))
    mocker.patch.object(redis_client, "get", return_value=None)
    mocker.patch.object(redis_client, "setex")

    response = client.get("/corpus/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["overview"]["total_nodes"] == 1
    assert "GitHub" in data["overview"]["sources"]
    assert any(kw["keyword"] == "Rag" for kw in data["keywords"]["top"])


def test_get_corpus_stats_redis_cache_hit(mocker):
    cached_payload = {
        "overview": {"total_nodes": 99, "sources": ["X"], "last_ingested": None, "date_range": {"from": None, "to": None}},
        "keywords": {"top": []},
        "by_source": {},
        "by_type": {},
    }
    mocker.patch.object(redis_client, "get", return_value=json.dumps(cached_payload))
    scroll_mock = mocker.patch.object(engine.client, "scroll")

    response = client.get("/corpus/stats")
    assert response.status_code == 200
    assert response.json()["overview"]["total_nodes"] == 99
    scroll_mock.assert_not_called()


def test_get_corpus_stats_caches_result(mocker):
    mocker.patch.object(engine.client, "scroll", return_value=([], None))
    mocker.patch.object(redis_client, "get", return_value=None)
    setex_mock = mocker.patch.object(redis_client, "setex")

    client.get("/corpus/stats")
    setex_mock.assert_called_once()
    args = setex_mock.call_args[0]
    assert args[0] == "corpus_stats"
    assert args[1] == 3600


def test_get_corpus_stats_qdrant_unreachable(mocker):
    mocker.patch.object(redis_client, "get", return_value=None)
    mocker.patch.object(engine.client, "scroll", side_effect=Exception("connection refused"))

    response = client.get("/corpus/stats")
    assert response.status_code == 503
