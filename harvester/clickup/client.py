import requests
import logging

logger = logging.getLogger("harvester.clickup.client")

class ClickUpClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url_v2 = "https://api.clickup.com/api/v2"
        self.base_url_v3 = "https://api.clickup.com/api/v3"
        self.headers = {
            "Authorization": self.api_key,
            "Accept": "application/json"
        }

    def _safe_get_list(self, response, key: str) -> list:
        """Safely extracts a flat list from a response, recursively flattening nested children."""
        try:
            data = response.json()
            root = data if isinstance(data, list) else data.get(key, []) if isinstance(data, dict) else []
            return self._flatten(root)
        except Exception as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return []

    def _flatten(self, nodes: list) -> list:
        """Recursively flatten a page tree into a flat list."""
        result = []
        for node in nodes:
            result.append(node)
            result.extend(self._flatten(node.get("pages", [])))
        return result

    def get_tasks(self, list_id: str, updated_since: str = None) -> list:
        url = f"{self.base_url_v2}/list/{list_id}/task"
        params = {}
        if updated_since:
            params["date_updated_gt"] = updated_since
        response = requests.get(url, headers=self.headers, params=params, timeout=30)
        response.raise_for_status()
        return self._safe_get_list(response, "tasks")

    def get_docs(self, workspace_id: str) -> list:
        """Returns all docs in the workspace using a single unfiltered sweep with cursor pagination.

        The parent_type filter causes ClickUp's API to cycle infinitely for FOLDER/LIST types
        and misses docs that are only visible without a filter, so we sweep without any filter.
        """
        url = f"{self.base_url_v3}/workspaces/{workspace_id}/docs"
        seen_ids: set[str] = set()
        all_docs = []
        cursor = None
        page = 0

        while True:
            params = {"limit": 100}
            if cursor:
                params["cursor"] = cursor
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            if response.status_code != 200:
                logger.debug(f"get_docs page {page}: status {response.status_code}")
                break
            data = response.json()
            docs = data.get("docs", [])
            new_ids = {d.get("id") for d in docs if d.get("id")} - seen_ids
            if not new_ids and docs:
                logger.warning(f"get_docs page {page}: cycle detected, stopping")
                break
            for doc in docs:
                if doc.get("id") and doc["id"] not in seen_ids:
                    seen_ids.add(doc["id"])
                    all_docs.append(doc)
            cursor = data.get("next_cursor")
            logger.debug(f"get_docs page {page}: {len(docs)} docs ({len(new_ids)} new), cursor={cursor!r}")
            page += 1
            if not cursor or not docs:
                break

        logger.info(f"get_docs: {len(all_docs)} unique docs found")
        return all_docs

    def get_page_by_id(self, workspace_id: str, doc_id: str, page_id: str) -> dict | None:
        """Fetch a single page by ID (used to fill gaps when get_pages truncates depth)."""
        possible_ids = [doc_id] if doc_id.startswith("d-") else [doc_id, f"d-{doc_id}"]
        for did in possible_ids:
            url = f"{self.base_url_v3}/workspaces/{workspace_id}/docs/{did}/pages/{page_id}"
            try:
                response = requests.get(url, headers=self.headers,
                                        params={"content_format": "text/md"}, timeout=30)
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                logger.warning(f"get_page_by_id({page_id}): {type(e).__name__}: {e}")
        return None

    def get_page_listing(self, workspace_id: str, doc_id: str) -> dict:
        """Returns the raw page listing tree for a doc (all depths)."""
        possible_ids = [doc_id]
        if not doc_id.startswith("d-"):
            possible_ids.append(f"d-{doc_id}")
        for pid in possible_ids:
            url = f"{self.base_url_v3}/workspaces/{workspace_id}/docs/{pid}/page_listing"
            try:
                response = requests.get(url, headers=self.headers, params={"max_page_depth": -1}, timeout=30)
            except Exception as e:
                logger.warning(f"get_page_listing({pid}): {type(e).__name__}: {e}")
                continue
            if response.status_code == 200:
                return response.json()
            logger.debug(f"get_page_listing({pid}): {response.status_code}")
        return {}

    def get_pages(self, workspace_id: str, doc_id: str) -> list:
        """Retrieves all pages in a document with fallback for IDs and errors."""
        # Ensure we try both raw and d-prefixed IDs
        possible_ids = [doc_id]
        if not doc_id.startswith("d-"):
            possible_ids.append(f"d-{doc_id}")

        for pid in possible_ids:
            url = f"{self.base_url_v3}/workspaces/{workspace_id}/docs/{pid}/pages"
            params = {"content_format": "text/md", "max_page_depth": -1}
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=30)

                if response.status_code == 404:
                    logger.warning(f"  get_pages({pid}): 404 — trying next ID variant")
                    continue

                if response.status_code >= 500:
                    logger.warning(f"  get_pages({pid}): {response.status_code} — {response.text[:200]}, retrying without depth")
                    params_limited = {"content_format": "text/md"}
                    response = requests.get(url, headers=self.headers, params=params_limited, timeout=30)
                    if response.status_code >= 500:
                        logger.warning(f"  get_pages({pid}) fallback: {response.status_code} — {response.text[:200]}")
                        continue

                if not response.ok:
                    logger.warning(f"  get_pages({pid}): {response.status_code} — {response.text[:200]}")
                    response.raise_for_status()

                return self._safe_get_list(response, "pages")
            except Exception as e:
                logger.warning(f"  get_pages({pid}): exception {type(e).__name__}: {e}")
                continue

        logger.warning(f"  Could not retrieve pages for doc {doc_id} after all retries.")
        return []

    def get_spaces(self, team_id: str) -> list:
        """Lists all spaces in a team/workspace."""
        url = f"{self.base_url_v2}/team/{team_id}/space"
        response = requests.get(url, headers=self.headers, timeout=30)
        response.raise_for_status()
        return self._safe_get_list(response, "spaces")

    def get_folders(self, space_id: str) -> list:
        """Lists all folders in a space."""
        url = f"{self.base_url_v2}/space/{space_id}/folder"
        response = requests.get(url, headers=self.headers, timeout=30)
        response.raise_for_status()
        return self._safe_get_list(response, "folders")

    def get_lists_in_folder(self, folder_id: str) -> list:
        """Lists all lists in a folder."""
        url = f"{self.base_url_v2}/folder/{folder_id}/list"
        response = requests.get(url, headers=self.headers, timeout=30)
        response.raise_for_status()
        return self._safe_get_list(response, "lists")

    def get_lists_in_space(self, space_id: str) -> list:
        """Lists all folderless lists in a space."""
        url = f"{self.base_url_v2}/space/{space_id}/list"
        response = requests.get(url, headers=self.headers, timeout=30)
        response.raise_for_status()
        return self._safe_get_list(response, "lists")
