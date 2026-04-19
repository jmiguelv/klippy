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

def test_get_markdown_files_returns_md_paths(mocker):
    tree = {
        "tree": [
            {"type": "blob", "path": "README.md"},
            {"type": "blob", "path": "docs/guide.md"},
            {"type": "blob", "path": "src/main.py"},
            {"type": "tree", "path": "docs"},
        ]
    }
    mocker.patch("requests.get", return_value=MockResponse(tree))

    client = GitHubClient(token="fake_token")
    files = client.get_markdown_files("owner/repo")

    assert len(files) == 2
    assert all(f["path"].endswith(".md") for f in files)


def test_get_file_content_decodes_base64(mocker):
    import base64
    encoded = base64.b64encode(b"# Hello").decode()
    mocker.patch("requests.get", return_value=MockResponse({"encoding": "base64", "content": encoded + "\n"}))

    client = GitHubClient(token="fake_token")
    content = client.get_file_content("owner/repo", "README.md")

    assert content == "# Hello"

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
