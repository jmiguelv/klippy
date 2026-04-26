import pytest
from fastapi.testclient import TestClient
from main import app, engine
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
    mock_point = mocker.Mock()
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
    mock_point = mocker.Mock()
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
    mock_point = mocker.Mock()
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
    mock_point = mocker.Mock()
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
