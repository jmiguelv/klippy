import requests

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
            # Use GitHub Link header for pagination
            if "next" in response.links:
                url = response.links["next"]["url"]
                params = None  # Params are included in the link URL
            else:
                url = None
        return results

    def get_commits(self, repo: str, since: str = None) -> list:
        url = f"{self.base_url}/repos/{repo}/commits"
        params = {}
        if since:
            params["since"] = since
        return self._get_paginated(url, params)

    def list_org_repos(self, org: str) -> list[str]:
        """Lists all public and private repositories for an organization."""
        url = f"{self.base_url}/orgs/{org}/repos"
        # By default, lists all types of repos.
        repos = self._get_paginated(url, {"per_page": 100})
        return [repo["full_name"] for repo in repos]

    def list_user_repos(self, user: str) -> list[str]:
        """Lists repositories for a specific user."""
        url = f"{self.base_url}/users/{user}/repos"
        repos = self._get_paginated(url, {"per_page": 100})
        return [repo["full_name"] for repo in repos]
