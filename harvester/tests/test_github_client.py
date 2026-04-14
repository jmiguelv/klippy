from github.client import GitHubClient

class MockResponse:
    def __init__(self, json_data, status_code=200, links=None):
        self.json_data = json_data
        self.status_code = status_code
        self.links = links or {}

    def json(self):
        return self.json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.exceptions.HTTPError("Error")

def test_get_readme(mocker):
    # Setup
    mock_response = MockResponse({
        "content": "IyBSRUFETUU=", # base64 for "# README"
        "encoding": "base64",
        "download_url": "https://raw.githubusercontent.com/owner/repo/main/README.md"
    })
    mocker.patch("requests.get", return_value=mock_response)

    client = GitHubClient(token="fake_token")
    
    # Execute
    readme = client.get_readme(repo="owner/repo")
    
    # Assert
    assert readme["content"] == "IyBSRUFETUU="
    assert readme["encoding"] == "base64"

def test_get_commits_returns_list_of_commits(mocker):
    mock_response = MockResponse([
        {
            "sha": "sha123",
            "commit": {"author": {"name": "a1", "date": "2021-06-01T20:00:00Z"}, "message": "m1"},
            "html_url": "url1"
        }
    ])
    mocker.patch("requests.get", return_value=mock_response)

    client = GitHubClient(token="fake_token")
    commits = client.get_commits(repo="owner/repo")
    
    assert len(commits) == 1
    assert commits[0]["sha"] == "sha123"

def test_list_org_repos(mocker):
    mock_response = MockResponse([{"full_name": "org/repo1"}])
    mocker.patch("requests.get", return_value=mock_response)

    client = GitHubClient(token="fake_token")
    repos = client.list_org_repos(org="my-org")
    
    assert len(repos) == 1
    assert repos[0] == "org/repo1"

def test_list_user_repos(mocker):
    mock_response = MockResponse([{"full_name": "user/repo1"}])
    mocker.patch("requests.get", return_value=mock_response)

    client = GitHubClient(token="fake_token")
    repos = client.list_user_repos(user="my-user")
    
    assert len(repos) == 1
    assert repos[0] == "user/repo1"
