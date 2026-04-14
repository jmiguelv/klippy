from unittest.mock import MagicMock
from orchestrator import Orchestrator

def test_orchestrator_runs_clickup(mocker):
    # Setup
    mock_clickup = MagicMock()
    mock_clickup.get_tasks.return_value = [{"id": "t1", "name": "Task 1"}]
    mock_clickup.get_docs.return_value = [{"id": "d1", "name": "Doc 1"}]
    mock_clickup.get_pages.return_value = [{"id": "p1", "name": "Page 1", "markdown": "content"}]
    
    mock_github = MagicMock()
    mock_github.list_org_repos.return_value = []
    
    # Mock parser to return a string
    mocker.patch("clickup.parser.task_to_markdown", return_value="task md")
    mocker.patch("clickup.parser.page_to_markdown", return_value="page md")
    
    # Mock file writing
    mock_write = mocker.patch("builtins.open", mocker.mock_open())
    mocker.patch("os.makedirs")
    
    orch = Orchestrator(clickup_client=mock_clickup, github_client=mock_github, data_dir="/tmp/data")
    
    # Execute
    orch.run_clickup(list_ids=["l1"], workspace_id="w1")
    
    # Assert
    assert mock_clickup.get_tasks.called
    assert mock_clickup.get_docs.called
    assert mock_write.called
