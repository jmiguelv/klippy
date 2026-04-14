import requests

class ClickUpClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url_v2 = "https://api.clickup.com/api/v2"
        self.base_url_v3 = "https://api.clickup.com/api/v3"
        self.headers = {
            "Authorization": self.api_key,
            "Accept": "application/json"
        }

    def get_tasks(self, list_id: str) -> list:
        url = f"{self.base_url_v2}/list/{list_id}/task"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json().get("tasks", [])

    def get_docs(self, workspace_id: str) -> list:
        """Retrieves all documents in a workspace using v3 API."""
        url = f"{self.base_url_v3}/workspaces/{workspace_id}/docs"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json().get("docs", [])

    def get_pages(self, workspace_id: str, doc_id: str) -> list:
        """Retrieves all pages in a document using v3 API, requesting markdown format."""
        url = f"{self.base_url_v3}/workspaces/{workspace_id}/docs/{doc_id}/pages"
        params = {"content_format": "text/md"}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json().get("pages", [])
