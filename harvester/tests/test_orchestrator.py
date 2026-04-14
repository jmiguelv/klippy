import pytest
from unittest.mock import MagicMock
from orchestrator import Orchestrator

def test_orchestrator_runs_clickup(mocker):
    # Setup
    mock_clickup = MagicMock()
    mock_clickup.get_spaces.return_value = [{"id": "s1", "name": "Space 1"}]
    mock_clickup.get_lists_in_space.return_value = [{"id": "l1", "name": "List 1"}]
    mock_clickup.get_folders.return_value = []
    mock_clickup.get_tasks.return_value = [{"id": "t1", "name": "Task 1"}]
    mock_clickup.get_docs.return_value = [{"id": "d1", "name": "Doc 1"}]
    mock_clickup.get_pages.return_value = [{"id": "p1", "name": "Page 1", "markdown": "content"}]
    
    mock_github = MagicMock()
    
    mock_state = MagicMock()
    
    # Mock parser to return a string
    mocker.patch("clickup.parser.task_to_markdown", return_value="task md")
    mocker.patch("clickup.parser.page_to_markdown", return_value="page md")
    
    # Mock file writing
    mock_write = mocker.patch("builtins.open", mocker.mock_open())
    mocker.patch("os.makedirs")
    
    orch = Orchestrator(clickup_client=mock_clickup, github_client=mock_github, state_store=mock_state, data_dir="/tmp/data")
    
    # Execute
    orch.run_clickup(workspace_id="w1", ignore_spaces=["ignored"])
    
    # Assert
    assert mock_clickup.get_spaces.called
    assert mock_clickup.get_tasks.called
    assert mock_clickup.get_docs.called
    assert mock_write.called

def test_orchestrator_runs_github(mocker):
    # Setup
    mock_clickup = MagicMock()
    
    mock_github = MagicMock()
    mock_github.list_org_repos.return_value = ["org/repo1"]
    mock_github.get_readme.return_value = {"content": "IyBSRUFETUU=", "html_url": "url"}
    mock_github.decode_content.return_value = "README content"
    mock_github.get_commits.return_value = [{"sha": "s1", "commit": {"author": {"name": "a1", "date": "d1"}, "message": "m1"}, "html_url": "u1"}]
    
    mock_state = MagicMock()
    mock_state.get_last_sync.return_value = None
    
    # Mock parser
    mocker.patch("github.parser.readme_to_markdown", return_value="readme md")
    mocker.patch("github.parser.commit_to_markdown", return_value="commit md")
    
    # Mock file writing
    mock_write = mocker.patch("builtins.open", mocker.mock_open())
    mocker.patch("os.makedirs")
    
    orch = Orchestrator(clickup_client=mock_clickup, github_client=mock_github, state_store=mock_state, data_dir="/tmp/data")
    
    # Execute
    orch.run_github(org_names=["my-org"])
    
    # Assert
    assert mock_github.list_org_repos.called
    assert mock_github.get_readme.called
    assert mock_github.get_commits.called
    assert mock_write.called
    assert mock_state.save.called
