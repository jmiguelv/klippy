from github.parser import commit_to_markdown, readme_to_markdown

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

def test_readme_to_markdown_basic():
    readme_content = "# Project X\nThis is a cool project."
    repo_name = "owner/project-x"
    url = "https://github.com/owner/project-x/blob/main/README.md"
    
    markdown = readme_to_markdown(readme_content, repo_name, url)
    
    assert "source: github" in markdown
    assert "type: readme" in markdown
    assert "repo: owner/project-x" in markdown
    assert "url: https://github.com/owner/project-x/blob/main/README.md" in markdown
    assert "# Project X" in markdown
    assert "This is a cool project." in markdown
