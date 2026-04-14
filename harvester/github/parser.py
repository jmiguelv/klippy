def commit_to_markdown(commit: dict, repo_name: str) -> str:
    """Converts a GitHub commit to Markdown with YAML frontmatter."""
    sha = commit.get("sha", "Unknown")
    commit_data = commit.get("commit", {})
    author = commit_data.get("author", {})
    message = commit_data.get("message", "No commit message.")
    url = commit.get("html_url", "")

    metadata = [
        "---",
        "source: github",
        "type: commit",
        f"repo: {repo_name}",
        f"sha: {sha}",
        f"author: {author.get('name', 'Unknown')}",
        f"date: {author.get('date', 'Unknown')}",
        f"url: {url}",
        "---",
        f"# Commit in {repo_name}",
        "",
        "## Message",
        "",
        message,
        ""
    ]
    return "\n".join(metadata)

def readme_to_markdown(content: str, repo_name: str, url: str) -> str:
    """Converts a GitHub README to Markdown with YAML frontmatter."""
    metadata = [
        "---",
        "source: github",
        "type: readme",
        f"repo: {repo_name}",
        f"url: {url}",
        "---",
        content
    ]
    return "\n".join(metadata)
