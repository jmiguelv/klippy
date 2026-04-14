from github.parser import commit_to_markdown

def test_commit_to_markdown_basic():
    commit = {
        "sha": "sha123",
        "commit": {
            "author": {"name": "John Doe", "date": "2021-06-01T20:00:00Z"},
            "message": "Feat: Add authentication"
        },
        "html_url": "https://github.com/owner/repo/commit/sha123"
    }
    
    markdown = commit_to_markdown(commit, "owner/repo")
    
    assert "source: github" in markdown
    assert "type: commit" in markdown
    assert "repo: owner/repo" in markdown
    assert "sha: sha123" in markdown
    assert "# Commit in owner/repo" in markdown
    assert "## Message" in markdown
    assert "Feat: Add authentication" in markdown
    assert "https://github.com/owner/repo/commit/sha123" in markdown
