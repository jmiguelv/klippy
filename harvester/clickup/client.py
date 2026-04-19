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
        """Safely extracts a list from a response, handling both dict and list results."""
        try:
            data = response.json()
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                return data.get(key, [])
            return []
        except Exception as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return []

    def get_tasks(self, list_id: str, updated_since: str = None) -> list:
        url = f"{self.base_url_v2}/list/{list_id}/task"
        params = {}
        if updated_since:
            params["date_updated_gt"] = updated_since
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return self._safe_get_list(response, "tasks")

    def get_docs(self, workspace_id: str) -> list:
        """Returns all top-level docs in the workspace by sweeping each parent type with cursor pagination."""
        url = f"{self.base_url_v3}/workspaces/{workspace_id}/docs"
        seen_ids: set[str] = set()
        all_docs = []

        for parent_type in ("WORKSPACE", "SPACE", "FOLDER", "LIST", "EVERYTHING"):
            cursor = None
            type_count = 0
            while True:
                params = {"limit": 100, "parent_type": parent_type}
                if cursor:
                    params["cursor"] = cursor
                response = requests.get(url, headers=self.headers, params=params)
                if response.status_code != 200:
                    logger.debug(f"get_docs({parent_type}): status {response.status_code}")
                    break
                data = response.json()
                docs = data.get("docs", [])
                for doc in docs:
                    if doc.get("id") and doc["id"] not in seen_ids:
                        seen_ids.add(doc["id"])
                        all_docs.append(doc)
                        type_count += 1
                cursor = data.get("cursor")
                logger.debug(f"get_docs({parent_type}): got {len(docs)} docs, cursor={cursor!r}")
                if not cursor or not docs:
                    break
            logger.info(f"get_docs({parent_type}): {type_count} new docs ({len(all_docs)} total)")

        logger.info(f"get_docs: {len(all_docs)} unique docs found across all parent types")
        return all_docs

    def get_page_listing(self, workspace_id: str, doc_id: str) -> dict:
        """Returns the raw page listing tree for a doc (all depths)."""
        possible_ids = [doc_id]
        if not doc_id.startswith("d-"):
            possible_ids.append(f"d-{doc_id}")
        for pid in possible_ids:
            url = f"{self.base_url_v3}/workspaces/{workspace_id}/docs/{pid}/page_listing"
            response = requests.get(url, headers=self.headers, params={"max_page_depth": -1})
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
                response = requests.get(url, headers=self.headers, params=params)

                if response.status_code == 404:
                    logger.warning(f"  get_pages({pid}): 404 — trying next ID variant")
                    continue

                if response.status_code >= 500:
                    logger.warning(f"  get_pages({pid}): {response.status_code} — {response.text[:200]}, retrying without depth")
                    params_limited = {"content_format": "text/md"}
                    response = requests.get(url, headers=self.headers, params=params_limited)
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
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return self._safe_get_list(response, "spaces")

    def get_folders(self, space_id: str) -> list:
        """Lists all folders in a space."""
        url = f"{self.base_url_v2}/space/{space_id}/folder"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return self._safe_get_list(response, "folders")

    def get_lists_in_folder(self, folder_id: str) -> list:
        """Lists all lists in a folder."""
        url = f"{self.base_url_v2}/folder/{folder_id}/list"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return self._safe_get_list(response, "lists")

    def get_lists_in_space(self, space_id: str) -> list:
        """Lists all folderless lists in a space."""
        url = f"{self.base_url_v2}/space/{space_id}/list"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return self._safe_get_list(response, "lists")
