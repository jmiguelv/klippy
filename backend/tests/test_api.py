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
    mock_point.payload = {
        metadata_key: "What is Klippy?\nHow to use it?\n"
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
        metadata_key: "Q1\nQ2\nQ3\nQ4\nQ5"
    }
    
    mocker.patch.object(engine.client, "scroll", return_value=([mock_point], None))
    
    response = client.get("/questions?n=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data["questions"]) == 3
    for q in data["questions"]:
        assert q in ["Q1", "Q2", "Q3", "Q4", "Q5"]

def test_get_questions_nested_metadata(mocker):
    metadata_key = "questions_this_excerpt_can_answer"
    mock_point = mocker.Mock()
    # No top-level metadata, only in _node_content
    mock_point.payload = {
        "_node_content": json.dumps({
            "metadata": {
                metadata_key: "Nested Question?"
            }
        })
    }
    
    mocker.patch.object(engine.client, "scroll", return_value=([mock_point], None))
    
    response = client.get("/questions?n=1")
    assert response.status_code == 200
    data = response.json()
    assert data["questions"] == ["Nested Question?"]
