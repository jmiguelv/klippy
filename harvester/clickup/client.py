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
        data = response.json()
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get(key, [])
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
        """Retrieves all documents in a workspace using v3 API."""
        url = f"{self.base_url_v3}/workspaces/{workspace_id}/docs"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return self._safe_get_list(response, "docs")

    def get_pages(self, workspace_id: str, doc_id: str) -> list:
        """Retrieves all pages in a document using v3 API, requesting markdown format."""
        url = f"{self.base_url_v3}/workspaces/{workspace_id}/docs/{doc_id}/pages"
        params = {"content_format": "text/md"}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return self._safe_get_list(response, "pages")

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
