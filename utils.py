import requests
import constants

class Github:
    def __init__(self):
        self.token = constants.GITHUB_TOKEN
        self.owner = constants.REPO_OWNER
        self.repo = constants.REPO_NAME

    def get_commit_info(self):
        url = f'https://api.github.com/repos/{self.owner}/{self.repo}/commits'
        headers = {
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {self.token}',
            'X-GitHub-Api-Version': '2022-11-28'
        }

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()