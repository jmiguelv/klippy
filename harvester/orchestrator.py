import os
import requests
import logging
from datetime import datetime
from clickup.parser import task_to_markdown, page_to_markdown
from github.parser import commit_to_markdown, readme_to_markdown

logger = logging.getLogger("harvester.orchestrator")

class Orchestrator:
    def __init__(self, clickup_client, github_client, state_store, data_dir: str):
        self.clickup = clickup_client
        self.github = github_client
        self.state = state_store
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    def _save_markdown(self, filename: str, content: str):
        """Helper to save markdown content to a file."""
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    def run_clickup(self, workspace_id: str, ignore_spaces: list[str] = None):
        """Orchestrates ClickUp ingestion by discovering all lists (excluding ignored spaces)."""
        ignore_spaces = [s.strip().lower() for s in (ignore_spaces or [])]
        
        # 1. Discover Spaces
        try:
            spaces = self.clickup.get_spaces(workspace_id)
        except Exception as e:
            logger.error(f"Failed to list spaces for workspace {workspace_id}: {e}")
            return

        all_list_ids = []
        for space in spaces:
            if space.get("name", "").lower() in ignore_spaces:
                logger.info(f"Ignoring space: {space['name']}")
                continue
            
            # 2. Discover Folders and Lists in Space
            space_id = space["id"]
            
            # Add folderless lists
            try:
                folderless_lists = self.clickup.get_lists_in_space(space_id)
                all_list_ids.extend([l["id"] for l in folderless_lists])
            except Exception as e:
                logger.warning(f"Failed to list folderless lists in space {space['name']}: {e}")

            # Add folders and their lists
            try:
                folders = self.clickup.get_folders(space_id)
                for folder in folders:
                    folder_lists = self.clickup.get_lists_in_folder(folder["id"])
                    all_list_ids.extend([l["id"] for l in folder_lists])
            except Exception as e:
                logger.warning(f"Failed to list folders in space {space['name']}: {e}")

        # 3. Process discovered Tasks
        for list_id in all_list_ids:
            try:
                tasks = self.clickup.get_tasks(list_id)
                for task in tasks:
                    md = task_to_markdown(task)
                    self._save_markdown(f"clickup_task_{task['id']}.md", md)
            except Exception as e:
                logger.warning(f"Failed to fetch tasks for list {list_id}: {e}")
        
        # 4. Process Docs & Pages (using Workspace ID)
        try:
            docs = self.clickup.get_docs(workspace_id)
            for doc in docs:
                doc_name = doc.get("name", "Untitled")
                pages = self.clickup.get_pages(workspace_id, doc["id"])
                for page in pages:
                    md = page_to_markdown(page, doc_name)
                    self._save_markdown(f"clickup_page_{page['id']}.md", md)
        except Exception as e:
            logger.warning(f"Failed to fetch docs for workspace {workspace_id}: {e}")

    def run_github(self, org_names: list[str] = None, user_names: list[str] = None):
        """Orchestrates GitHub ingestion with incremental sync."""
        repos = []
        if org_names:
            for org in org_names:
                repos.extend(self.github.list_org_repos(org))
        if user_names:
            for user in user_names:
                repos.extend(self.github.list_user_repos(user))

        current_sync_time = datetime.now().isoformat()

        for repo in repos:
            # README full sync
            try:
                readme_data = self.github.get_readme(repo)
                raw_content = self.github.decode_content(readme_data["content"])
                md = readme_to_markdown(raw_content, repo, readme_data.get("html_url", ""))
                safe_repo_name = repo.replace("/", "_")
                self._save_markdown(f"github_readme_{safe_repo_name}.md", md)
            except requests.exceptions.HTTPError:
                pass

            # Commits Incremental
            last_sync = self.state.get_last_sync(f"github_repo_{repo}")
            commits = self.github.get_commits(repo, since=last_sync)
            for commit in commits:
                md = commit_to_markdown(commit, repo)
                safe_repo_name = repo.replace("/", "_")
                self._save_markdown(f"github_commit_{safe_repo_name}_{commit['sha']}.md", md)
            
            self.state.set_last_sync(f"github_repo_{repo}", current_sync_time)
        
        self.state.save()
