import os
from clickup.parser import task_to_markdown, page_to_markdown
from github.parser import commit_to_markdown

class Orchestrator:
    def __init__(self, clickup_client, github_client, data_dir: str):
        self.clickup = clickup_client
        self.github = github_client
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    def _save_markdown(self, filename: str, content: str):
        """Helper to save markdown content to a file."""
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    def run_clickup(self, list_ids: list[str], workspace_id: str):
        """Orchestrates ClickUp ingestion."""
        # Process Tasks
        for list_id in list_ids:
            tasks = self.clickup.get_tasks(list_id)
            for task in tasks:
                md = task_to_markdown(task)
                self._save_markdown(f"clickup_task_{task['id']}.md", md)
        
        # Process Docs & Pages
        docs = self.clickup.get_docs(workspace_id)
        for doc in docs:
            doc_name = doc.get("name", "Untitled")
            pages = self.clickup.get_pages(workspace_id, doc["id"])
            for page in pages:
                md = page_to_markdown(page, doc_name)
                self._save_markdown(f"clickup_page_{page['id']}.md", md)

    def run_github(self, org_names: list[str] = None, user_names: list[str] = None):
        """Orchestrates GitHub ingestion."""
        repos = []
        if org_names:
            for org in org_names:
                repos.extend(self.github.list_org_repos(org))
        if user_names:
            for user in user_names:
                repos.extend(self.github.list_user_repos(user))

        for repo in repos:
            commits = self.github.get_commits(repo)
            for commit in commits:
                md = commit_to_markdown(commit, repo)
                # Use safe filename for repo (org_repo_sha)
                safe_repo_name = repo.replace("/", "_")
                self._save_markdown(f"github_commit_{safe_repo_name}_{commit['sha']}.md", md)
