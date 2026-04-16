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
        logger.debug(f"Saving file: {filename}")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    def run_clickup(self, workspace_id: str, ignore_spaces: list[str] = None, force: bool = False):
        """Orchestrates ClickUp ingestion by discovering all lists (excluding ignored spaces)."""
        logger.info(f"Starting ClickUp harvesting for workspace: {workspace_id} (force={force})")
        ignore_spaces = [s.strip().lower() for s in (ignore_spaces or [])]
        
        try:
            spaces = self.clickup.get_spaces(workspace_id)
            logger.info(f"Discovered {len(spaces)} spaces.")
        except Exception as e:
            logger.error(f"Failed to list spaces: {e}")
            return

        all_lists = [] # Store tuple of (list_id, list_name, folder_name, space_name)
        for space in spaces:
            if not isinstance(space, dict): continue
            space_name = space.get("name", "Unknown")
            if space_name.lower() in ignore_spaces:
                logger.info(f"Skipping ignored space: {space_name}")
                continue
            
            logger.info(f"Processing space: {space_name}")
            space_id = space["id"]
            
            # Folderless lists
            try:
                folderless_lists = self.clickup.get_lists_in_space(space_id)
                for l in folderless_lists:
                    if isinstance(l, dict):
                        all_lists.append((l["id"], l.get("name", "Untitled"), "None", space_name))
                if folderless_lists:
                    logger.info(f"  Found {len(folderless_lists)} folderless lists.")
            except Exception as e:
                logger.warning(f"  Failed to list folderless lists: {e}")

            # Folders
            try:
                folders = self.clickup.get_folders(space_id)
                for folder in folders:
                    if not isinstance(folder, dict): continue
                    logger.info(f"  Processing folder: {folder.get('name', 'Untitled')}")
                    folder_lists = self.clickup.get_lists_in_folder(folder["id"])
                    for l in folder_lists:
                        if isinstance(l, dict):
                            all_lists.append((l["id"], l.get("name", "Untitled"), folder.get('name', 'Untitled'), space_name))
            except Exception as e:
                logger.warning(f"  Failed to list folders: {e}")

        logger.info(f"Discovered a total of {len(all_lists)} lists. Fetching tasks...")
        # 3. Process discovered Tasks
        current_sync_time_ms = str(int(datetime.now().timestamp() * 1000))
        task_count = 0
        for list_id, list_name, folder_name, space_name in all_lists:
            try:
                last_sync = None if force else self.state.get_last_sync(f"clickup_list_{list_id}")
                tasks = self.clickup.get_tasks(list_id, updated_since=last_sync)
                for task in tasks:
                    if isinstance(task, dict):
                        md = task_to_markdown(task, space_name=space_name, folder_name=folder_name, list_name=list_name)
                        self._save_markdown(f"clickup_task_{task['id']}.md", md)
                        task_count += 1

                # Save state for THIS list
                self.state.set_last_sync(f"clickup_list_{list_id}", current_sync_time_ms)
                self.state.save()
            except Exception as e:
                logger.warning(f"Failed to fetch tasks for list {list_id}: {e}")
        
        logger.info(f"Successfully harvested {task_count} ClickUp tasks.")

        # 4. Process Docs & Pages (using Workspace ID)
        logger.info("Fetching ClickUp Docs and Pages...")
        try:
            docs = self.clickup.get_docs(workspace_id)
            doc_count = 0
            page_count = 0
            if isinstance(docs, list):
                for doc in docs:
                    if not isinstance(doc, dict): continue
                    doc_name = doc.get("name", "Untitled")
                    doc_id = doc.get("id")
                    if not doc_id: continue
                    
                    pages = self.clickup.get_pages(workspace_id, doc_id)
                    doc_count += 1
                    if isinstance(pages, list):
                        for page in pages:
                            if not isinstance(page, dict): continue
                            page_id = page.get("id")
                            if not page_id: continue
                            md = page_to_markdown(page, doc_name, workspace_id=workspace_id)
                            self._save_markdown(f"clickup_page_{page_id}.md", md)
                            page_count += 1
            logger.info(f"Harvested {page_count} pages from {doc_count} docs.")
        except Exception as e:
            logger.error(f"Failed to fetch docs: {e}", exc_info=True)

    def run_github(self, org_names: list[str] = None, user_names: list[str] = None, force: bool = False):
        """Orchestrates GitHub ingestion with incremental sync."""
        logger.info(f"Starting GitHub harvesting (force={force})...")
        repos = []
        if org_names:
            for org in org_names:
                logger.info(f"Discovering repos for organization: {org}")
                repos.extend(self.github.list_org_repos(org))
        if user_names:
            for user in user_names:
                logger.info(f"Discovering repos for user: {user}")
                repos.extend(self.github.list_user_repos(user))

        logger.info(f"Found {len(repos)} repositories. Starting content sync...")
        current_sync_time = datetime.now().isoformat()

        for repo in repos:
            logger.info(f"Processing repository: {repo}")
            # README full sync
            try:
                readme_data = self.github.get_readme(repo)
                if isinstance(readme_data, dict):
                    raw_content = self.github.decode_content(readme_data["content"])
                    md = readme_to_markdown(raw_content, repo, readme_data.get("html_url", ""))
                    safe_repo_name = repo.replace("/", "_")
                    self._save_markdown(f"github_readme_{safe_repo_name}.md", md)
                    logger.info(f"  ✓ Harvested README")
            except Exception:
                logger.debug(f"  - No README found for {repo}")

            # Commits Incremental
            last_sync = None if force else self.state.get_last_sync(f"github_repo_{repo}")
            logger.info(f"  Fetching commits since {last_sync or 'the beginning'}...")
            try:
                commits = self.github.get_commits(repo, since=last_sync)
                if isinstance(commits, list):
                    for commit in commits:
                        if isinstance(commit, dict):
                            md = commit_to_markdown(commit, repo)
                            safe_repo_name = repo.replace("/", "_")
                            self._save_markdown(f"github_commit_{safe_repo_name}_{commit['sha']}.md", md)
                    logger.info(f"  ✓ Harvested {len(commits)} commits")

                    # Save state for THIS repo immediately
                    self.state.set_last_sync(f"github_repo_{repo}", current_sync_time)
                    self.state.save()
            except Exception as e:
                logger.error(f"  Failed to fetch commits for {repo}: {e}")

        logger.info("GitHub harvesting complete.")
