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
        """Retrieves all documents in a workspace by searching across all parent types."""
        url = f"{self.base_url_v3}/workspaces/{workspace_id}/docs"
        all_docs = []
        
        parent_types = ["WORKSPACE", "SPACE", "FOLDER", "LIST"]
        
        for p_type in parent_types:
            logger.info(f"  Searching for docs with parent_type: {p_type}")
            cursor = None
            type_doc_count = 0
            
            while True:
                params = {"limit": 100, "parent_type": p_type}
                if cursor:
                    params["cursor"] = cursor
                
                response = requests.get(url, headers=self.headers, params=params)
                if response.status_code != 200:
                    logger.debug(f"    No docs found or error for type {p_type}")
                    break
                    
                data = response.json()
                docs = data.get("docs", [])
                
                for doc in docs:
                    if doc.get("id") not in [d.get("id") for d in all_docs]:
                        all_docs.append(doc)
                        type_doc_count += 1
                
                cursor = data.get("cursor")
                if not cursor or not docs:
                    break
            
            if type_doc_count > 0:
                logger.info(f"    Found {type_doc_count} docs.")
                
        return all_docs

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
                    continue # Try next ID
                    
                if response.status_code >= 500:
                    # Fallback to depth 0
                    params_limited = {"content_format": "text/md"}
                    response = requests.get(url, headers=self.headers, params=params_limited)
                    if response.status_code >= 500:
                        continue # Skip this ID

                response.raise_for_status()
                return self._safe_get_list(response, "pages")
            except Exception:
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
