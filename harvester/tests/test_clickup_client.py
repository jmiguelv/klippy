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
    # No parent_type filter — single unfiltered sweep
    assert "parent_type" not in mock_get.call_args[1]["params"]


def test_get_docs_paginates_with_next_cursor(mocker):
    # ClickUp v3 API uses "next_cursor" for pagination tokens
    first_page = {"docs": [{"id": "doc1"}], "next_cursor": "tok"}
    second_page = {"docs": [{"id": "doc2"}]}

    mock_get = mocker.patch("requests.get")
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.side_effect = [first_page, second_page]

    client = ClickUpClient(api_key="fake_key")
    docs = client.get_docs(workspace_id="ws1")

    assert len(docs) == 2
    assert mock_get.call_args_list[1][1]["params"]["cursor"] == "tok"


def test_get_docs_stops_on_cycle(mocker):
    # If the API returns only already-seen IDs, pagination must stop
    page = {"docs": [{"id": "doc1"}], "next_cursor": "tok"}

    mock_get = mocker.patch("requests.get")
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.side_effect = [page, page, page]  # same doc repeating

    client = ClickUpClient(api_key="fake_key")
    docs = client.get_docs(workspace_id="ws1")

    assert len(docs) == 1  # deduplicated, stops after cycle detected
    assert mock_get.call_count == 2  # first call + one cycle-detected call, then stops


def test_get_page_by_id_returns_page(mocker):
    mock_response = {"id": "p99", "name": "Deep page", "content": "hello"}
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = mock_response

    client = ClickUpClient(api_key="fake_key")
    page = client.get_page_by_id(workspace_id="ws1", doc_id="doc1", page_id="p99")

    assert page["id"] == "p99"
    assert "pages/p99" in mock_get.call_args[0][0]


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
    mock_response = {
        "pages": [
            {"id": "page456", "name": "Overview", "content": "Welcome", "markdown": "Welcome md"}
        ]
    }
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = mock_response

    client = ClickUpClient(api_key="fake_key")
    pages = client.get_pages(workspace_id="team123", doc_id="doc123")

    assert len(pages) == 1
    assert pages[0]["id"] == "page456"
    assert pages[0]["markdown"] == "Welcome md"


def test_get_pages_flattens_nested_pages(mocker):
    # ClickUp returns a tree; all descendants must be included in the flat result
    mock_response = {
        "pages": [
            {
                "id": "p1", "name": "Top",
                "pages": [
                    {
                        "id": "p1a", "name": "Child",
                        "pages": [
                            {"id": "p1a1", "name": "Grandchild"}
                        ]
                    }
                ]
            }
        ]
    }
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = mock_response

    client = ClickUpClient(api_key="fake_key")
    pages = client.get_pages(workspace_id="team123", doc_id="doc123")

    assert {p["id"] for p in pages} == {"p1", "p1a", "p1a1"}

def test_get_pages_paginates_with_next_cursor(mocker):
    first_page = {"pages": [{"id": "p1"}], "next_cursor": "tok"}
    second_page = {"pages": [{"id": "p2"}]}

    mock_get = mocker.patch("requests.get")
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.side_effect = [first_page, second_page]

    client = ClickUpClient(api_key="fake_key")
    pages = client.get_pages(workspace_id="ws1", doc_id="doc1")

    assert len(pages) == 2
    assert {p["id"] for p in pages} == {"p1", "p2"}
    assert mock_get.call_args_list[1][1]["params"]["cursor"] == "tok"

def test_get_page_listing_paginates_with_next_cursor(mocker):
    first_page = {"pages": [{"id": "p1"}], "next_cursor": "tok"}
    second_page = {"pages": [{"id": "p2"}]}

    mock_get = mocker.patch("requests.get")
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.side_effect = [first_page, second_page]

    client = ClickUpClient(api_key="fake_key")
    listing = client.get_page_listing(workspace_id="ws1", doc_id="doc1")

    assert "pages" in listing
    assert len(listing["pages"]) == 2
    assert {p["id"] for p in listing["pages"]} == {"p1", "p2"}

def test_get_docs_supports_parent_filters(mocker):
    mock_response = {"docs": [{"id": "doc1"}]}
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = mock_response

    client = ClickUpClient(api_key="fake_key")
    client.get_docs(workspace_id="ws1", parent_id="space123", parent_type="SPACE")

    params = mock_get.call_args[1]["params"]
    assert params["parent_id"] == "space123"
    assert params["parent_type"] == "SPACE"
