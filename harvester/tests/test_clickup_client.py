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
    mock_response = {"docs": [{"id": "doc123", "name": "Project Plan"}]}
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = mock_response

    client = ClickUpClient(api_key="fake_key")
    docs = client.get_docs(workspace_id="team123")

    assert len(docs) == 1
    assert docs[0]["id"] == "doc123"
    assert docs[0]["name"] == "Project Plan"
    # Must sweep all five parent types
    used_types = {call[1]["params"]["parent_type"] for call in mock_get.call_args_list}
    assert used_types == {"WORKSPACE", "SPACE", "FOLDER", "LIST", "EVERYTHING"}


def test_get_docs_paginates_with_cursor(mocker):
    # First parent_type returns two pages; remaining three return empty
    first_page = {"docs": [{"id": "doc1"}], "cursor": "tok"}
    second_page = {"docs": [{"id": "doc2"}]}
    empty = {"docs": []}

    mock_get = mocker.patch("requests.get")
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.side_effect = [first_page, second_page, empty, empty, empty, empty]

    client = ClickUpClient(api_key="fake_key")
    docs = client.get_docs(workspace_id="ws1")

    assert len(docs) == 2
    # Second call must carry the cursor
    assert mock_get.call_args_list[1][1]["params"]["cursor"] == "tok"


def test_get_page_listing_returns_raw_data(mocker):
    mock_response = {"pages": [{"id": "p1", "doc_id": "d1", "children": []}]}
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = mock_response

    client = ClickUpClient(api_key="fake_key")
    listing = client.get_page_listing(workspace_id="ws1", doc_id="doc1")

    assert listing == mock_response
    assert "page_listing" in mock_get.call_args[0][0]

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
