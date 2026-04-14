from datetime import datetime

def format_timestamp(ts: str) -> str:
    """Helper to format ClickUp timestamp."""
    try:
        return datetime.fromtimestamp(int(ts) / 1000).strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        return "Unknown"

def task_to_markdown(task: dict) -> str:
    """Converts a ClickUp task to Markdown with YAML frontmatter."""
    metadata = [
        "---",
        "source: clickup",
        "type: task",
        f"id: {task.get('id')}",
        f"status: {task.get('status', {}).get('status')}",
        f"url: {task.get('url')}",
        f"creator: {task.get('creator', {}).get('username')}",
        f"created_at: {format_timestamp(task.get('date_created'))}",
        f"updated_at: {format_timestamp(task.get('date_updated'))}",
        f"assignees: {', '.join(a.get('username', '') for a in task.get('assignees', []))}",
        "---",
        f"# {task.get('name', 'Untitled Task')}",
        "",
        "## Description",
        "",
        task.get('description', 'No description.'),
        ""
    ]
    return "\n".join(metadata)

def page_to_markdown(page: dict, doc_name: str) -> str:
    """Converts a ClickUp Page to Markdown with YAML frontmatter."""
    metadata = [
        "---",
        "source: clickup",
        "type: page",
        f"id: {page.get('id')}",
        f"doc_name: {doc_name}",
        f"created_at: {format_timestamp(page.get('date_created'))}",
        f"updated_at: {format_timestamp(page.get('date_updated'))}",
        "---",
        f"# {doc_name} / {page.get('name', 'Untitled Page')}",
        "",
        page.get("markdown", page.get("content", "")),
        ""
    ]
    return "\n".join(metadata)
