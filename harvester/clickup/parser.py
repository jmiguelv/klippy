from datetime import datetime

def format_timestamp(ts: str) -> str:
    """Helper to format ClickUp timestamp."""
    try:
        return datetime.fromtimestamp(int(ts) / 1000).strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        return "Unknown"

def task_to_markdown(task: dict, space_name: str = "Unknown", folder_name: str = "Unknown", list_name: str = "Unknown") -> str:
    """Converts a ClickUp task to Markdown with YAML frontmatter."""
    creator = task.get('creator', {}) or {}
    creator_name = creator.get('username') or 'Unknown'
    
    assignees = task.get('assignees', []) or []
    assignee_names = [a.get('username') for a in assignees if a and a.get('username')]
    
    status_info = task.get('status', {}) or {}
    status_name = status_info.get('status') or 'Unknown'
    
    metadata = [
        "---",
        "source: clickup",
        "type: task",
        f"id: {task.get('id')}",
        f"space: {space_name}",
        f"folder: {folder_name}",
        f"list: {list_name}",
        f"status: {status_name}",
        f"url: {task.get('url')}",
        f"creator: {creator_name}",
        f"created_at: {format_timestamp(task.get('date_created'))}",
        f"updated_at: {format_timestamp(task.get('date_updated'))}",
        f"assignees: {', '.join(assignee_names)}",
        "---",
        f"# {task.get('name', 'Untitled Task')}",
        "",
        "## Description",
        "",
        task.get('description') or 'No description.',
        ""
    ]
    return "\n".join(metadata)

def page_to_markdown(page: dict, doc_name: str, workspace_id: str = "Unknown") -> str:
    """Converts a ClickUp Page to Markdown with YAML frontmatter."""
    metadata = [
        "---",
        "source: clickup",
        "type: page",
        f"id: {page.get('id')}",
        f"workspace: {workspace_id}",
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
