import os
import json
import logging
from datetime import datetime
from clickup.parser import task_to_markdown, page_to_markdown
from github.parser import readme_to_markdown

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

    def run_clickup(self, workspace_id: str, ignore_spaces: list[str] = None, force: bool = False, docs_only: bool = False):
        """Orchestrates ClickUp ingestion with deep document discovery."""
        logger.info(f"Starting ClickUp harvesting for workspace: {workspace_id} (force={force}, docs_only={docs_only})")
        
        # 1. Discover Containers (Spaces, Folders, Lists)
        try:
            spaces = self.clickup.get_spaces(workspace_id)
        except Exception as e:
            logger.error(f"Failed to list spaces: {e}")
            return

        all_lists = []
        all_doc_containers = [("WORKSPACE", workspace_id)] # List of (type, id)
        
        ignore_spaces = [s.strip().lower() for s in (ignore_spaces or [])]
        
        for space in spaces:
            if not isinstance(space, dict): continue
            space_name = space.get("name", "Unknown")
            if space_name.lower() in ignore_spaces:
                continue
            
            space_id = space["id"]
            all_doc_containers.append(("SPACE", space_id))
            
            # Folderless lists
            try:
                folderless_lists = self.clickup.get_lists_in_space(space_id)
                for l in folderless_lists:
                    if isinstance(l, dict):
                        all_lists.append((l["id"], l.get("name", "Untitled"), "None", space_name))
            except Exception: pass

            # Folders
            try:
                folders = self.clickup.get_folders(space_id)
                for folder in folders:
                    if not isinstance(folder, dict): continue
                    all_doc_containers.append(("FOLDER", folder["id"]))
                    folder_lists = self.clickup.get_lists_in_folder(folder["id"])
                    for l in folder_lists:
                        if isinstance(l, dict):
                            all_lists.append((l["id"], l.get("name", "Untitled"), folder.get('name', 'Untitled'), space_name))
            except Exception: pass

        # 2. Process Tasks (if not docs_only)
        if not docs_only:
            logger.info(f"Discovered {len(all_lists)} lists. Fetching tasks...")
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
                    self.state.set_last_sync(f"clickup_list_{list_id}", current_sync_time_ms)
                    self.state.save()
                except Exception as e:
                    logger.warning(f"Failed tasks for {list_id}: {e}")
            logger.info(f"Harvested {task_count} tasks.")

        # 3. Deep Document Discovery
        logger.info("Starting deep document discovery...")
        seen_doc_ids: set[str] = set()
        doc_count = 0
        page_count = 0

        try:
            initial_docs = self.clickup.get_docs(workspace_id)
        except Exception as e:
            logger.error(f"get_docs failed: {e}")
            initial_docs = []

        logger.info(f"get_docs returned {len(initial_docs)} docs: {[d.get('id') for d in initial_docs]}")
        queue = [d for d in initial_docs if d.get("id") and not seen_doc_ids.add(d["id"])]

        _listing_logged = False

        def _walk_listing(nodes, doc_id):
            """Walk page listing tree; enqueue any sub-docs (items with a different doc_id)."""
            for node in (nodes or []):
                node_doc_id = node.get("doc_id")
                if node_doc_id and node_doc_id != doc_id and node_doc_id not in seen_doc_ids:
                    logger.info(f"  Found sub-doc {node_doc_id} ('{node.get('name')}') in listing of {doc_id}")
                    seen_doc_ids.add(node_doc_id)
                    queue.append({"id": node_doc_id, "name": node.get("name", "Untitled")})
                # Nested pages are under the "pages" key
                _walk_listing(node.get("pages", []), doc_id)

        def _all_listing_ids(nodes):
            """Collect every page ID in the listing tree at all depths."""
            ids = set()
            for node in (nodes or []):
                if node.get("id"):
                    ids.add(node["id"])
                ids |= _all_listing_ids(node.get("pages", []))
            return ids

        # BFS: harvest pages and discover sub-docs via page listing
        while queue:
            d = queue.pop(0)
            doc_id = d["id"]

            try:
                pages = self.clickup.get_pages(workspace_id, doc_id)
            except Exception as e:
                logger.warning(f"Could not harvest pages for doc {doc_id}: {e}")
                pages = []

            # Use page listing to discover sub-docs and fill depth gaps in get_pages
            listing = self.clickup.get_page_listing(workspace_id, doc_id)
            if not _listing_logged and listing:
                logger.info(f"Page listing sample (doc {doc_id}): {json.dumps(listing)[:800]}")
                _listing_logged = True
            pages_root = listing if isinstance(listing, list) else listing.get("pages", [])
            _walk_listing(pages_root, doc_id)

            # Fetch any pages in the listing not returned by get_pages (API depth limit)
            fetched_ids = {p["id"] for p in pages if p.get("id")}
            for pid in _all_listing_ids(pages_root) - fetched_ids:
                page = self.clickup.get_page_by_id(workspace_id, doc_id, pid)
                if page:
                    pages.append(page)

            if pages:
                doc_count += 1
                for p in pages:
                    md = page_to_markdown(p, d.get("name", "Untitled"), workspace_id=workspace_id)
                    self._save_markdown(f"clickup_page_{p['id']}.md", md)
                    page_count += 1

        logger.info(f"Final: {page_count} pages from {doc_count} docs ({len(seen_doc_ids)} total discovered).")

    def run_github(self, org_names: list[str] = None, user_names: list[str] = None,
                   force: bool = False, ignore_repos: list[str] = None):
        """Orchestrates GitHub ingestion by harvesting all markdown files from each repo."""
        logger.info(f"Starting GitHub harvesting (force={force})...")
        ignore_repos = {r.strip().lower() for r in (ignore_repos or [])}
        repos = []
        if org_names:
            for org in org_names:
                repos.extend(self.github.list_org_repos(org))
        if user_names:
            for user in user_names:
                repos.extend(self.github.list_user_repos(user))

        file_count = 0
        for repo in repos:
            if repo.lower() in ignore_repos:
                logger.info(f"Skipping ignored repo: {repo}")
                continue
            md_files = self.github.get_markdown_files(repo)
            logger.info(f"{repo}: {len(md_files)} markdown files found")
            for item in md_files:
                path = item["path"]
                try:
                    content = self.github.get_file_content(repo, path)
                    if not content:
                        continue
                    html_url = f"https://github.com/{repo}/blob/HEAD/{path}"
                    md = readme_to_markdown(content, repo, html_url)
                    safe_name = repo.replace("/", "_") + "_" + path.replace("/", "_")
                    self._save_markdown(f"github_md_{safe_name}", md)
                    file_count += 1
                except Exception as e:
                    logger.warning(f"Failed to fetch {repo}/{path}: {e}")

        logger.info(f"GitHub harvesting complete. {file_count} markdown files harvested.")
