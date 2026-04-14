from clickup.parser import task_to_markdown, page_to_markdown

def test_task_to_markdown_basic():
    task = {
        "id": "abc",
        "name": "Task 1",
        "description": "This is a description",
        "status": {"status": "in progress"},
        "url": "https://app.clickup.com/t/abc",
        "creator": {"username": "John Doe"},
        "date_created": "1622548800000",
        "date_updated": "1622548800000",
        "assignees": [{"username": "Jane Doe"}]
    }
    
    markdown = task_to_markdown(task, space_name="My Space", folder_name="My Folder", list_name="My List")
    
    assert "source: clickup" in markdown
    assert "space: My Space" in markdown
    assert "folder: My Folder" in markdown
    assert "list: My List" in markdown
    assert "type: task" in markdown
    assert "id: abc" in markdown
    assert "status: in progress" in markdown
    assert "creator: John Doe" in markdown
    assert "assignees: Jane Doe" in markdown
    assert "# Task 1" in markdown

def test_task_to_markdown_with_nones():
    task = {
        "id": "abc",
        "name": "Task 1",
        "description": None,
        "status": None,
        "url": None,
        "creator": {"username": None},
        "date_created": None,
        "date_updated": None,
        "assignees": [{"username": None}, None]
    }
    
    markdown = task_to_markdown(task)
    
    assert "creator: Unknown" in markdown
    assert "space: Unknown" in markdown
    assert "assignees: " in markdown # Should be empty join
    assert "No description." in markdown

def test_page_to_markdown_basic():
    page = {
        "id": "page123",
        "name": "Project Overview",
        "markdown": "## Content\nThis is the content.",
        "date_created": "1622548800000",
        "date_updated": "1622548800000"
    }
    doc_name = "Team Handbook"
    
    markdown = page_to_markdown(page, doc_name, workspace_id="w123")
    
    assert "source: clickup" in markdown
    assert "type: page" in markdown
    assert "id: page123" in markdown
    assert "workspace: w123" in markdown
    assert "doc_name: Team Handbook" in markdown
    assert "# Team Handbook / Project Overview" in markdown
    assert "## Content" in markdown
    assert "This is the content." in markdown
