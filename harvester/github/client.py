import requests
import base64

class GitHubClient:
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def _get_paginated(self, url: str, params: dict = None) -> list:
        """Helper to handle paginated GitHub requests."""
        results = []
        while url:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            results.extend(response.json())
            if "next" in response.links:
                url = response.links["next"]["url"]
                params = None
            else:
                url = None
        return results

    def get_markdown_files(self, repo: str) -> list[dict]:
        """Returns all .md files in a repo using the Git Trees API (recursive)."""
        url = f"{self.base_url}/repos/{repo}/git/trees/HEAD"
        response = requests.get(url, headers=self.headers, params={"recursive": "1"})
        if response.status_code != 200:
            import logging
            logging.getLogger("harvester.github.client").warning(
                f"get_markdown_files({repo}): status {response.status_code}"
            )
            return []
        tree = response.json().get("tree", [])
        return [item for item in tree if item.get("type") == "blob" and item.get("path", "").endswith(".md")]

    def get_file_content(self, repo: str, path: str) -> str | None:
        """Returns decoded content of a file, or None on failure."""
        url = f"{self.base_url}/repos/{repo}/contents/{path}"
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            return None
        data = response.json()
        if isinstance(data, dict) and data.get("encoding") == "base64":
            return self.decode_content(data["content"])
        return None

    def list_org_repos(self, org: str) -> list[str]:
        """Lists all repositories for an organization."""
        url = f"{self.base_url}/orgs/{org}/repos"
        repos = self._get_paginated(url, {"per_page": 100})
        return [repo["full_name"] for repo in repos]

    def list_user_repos(self, user: str) -> list[str]:
        """Lists repositories for a specific user."""
        url = f"{self.base_url}/users/{user}/repos"
        repos = self._get_paginated(url, {"per_page": 100})
        return [repo["full_name"] for repo in repos]

    def decode_content(self, content: str) -> str:
        """Decodes base64 content."""
        return base64.b64decode(content).decode("utf-8")
