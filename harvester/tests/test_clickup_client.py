from clickup.client import ClickUpClient

def test_get_tasks_returns_list_of_tasks(mocker):
    # Setup
    mock_response = {
        "tasks": [
            {
                "id": "abc",
                "name": "Task 1",
                "description": "Desc 1",
                "status": {"status": "open"},
                "date_created": "1622548800000",
                "date_updated": "1622548800000",
                "creator": {"username": "user1"},
                "assignees": [],
                "url": "https://app.clickup.com/t/abc"
            }
        ]
    }
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = mock_response

    client = ClickUpClient(api_key="fake_key")
    
    # Execute
    tasks = client.get_tasks(list_id="123")
    
    # Assert
    assert len(tasks) == 1
    assert tasks[0]["id"] == "abc"
    assert tasks[0]["name"] == "Task 1"

def test_get_docs_returns_list_of_docs(mocker):
    # Setup
    mock_response = {
        "docs": [
            {"id": "doc123", "name": "Project Plan"}
        ]
    }
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = mock_response

    client = ClickUpClient(api_key="fake_key")
    
    # Execute
    docs = client.get_docs(workspace_id="team123")
    
    # Assert
    assert len(docs) == 1
    assert docs[0]["id"] == "doc123"
    assert docs[0]["name"] == "Project Plan"

def test_get_pages_returns_list_of_pages(mocker):
    # Setup
    mock_response = {
        "pages": [
            {"id": "page456", "name": "Overview", "content": "Welcome", "markdown": "Welcome md"}
        ]
    }
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = mock_response

    client = ClickUpClient(api_key="fake_key")
    
    # Execute
    pages = client.get_pages(workspace_id="team123", doc_id="doc123")
    
    # Assert
    assert len(pages) == 1
    assert pages[0]["id"] == "page456"
    assert pages[0]["markdown"] == "Welcome md"
