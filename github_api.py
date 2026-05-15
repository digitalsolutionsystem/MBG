import requests

def create_repo(token, repo_name, private=False):
    url = "https://api.github.com/user/repos"
    headers = {"Authorization": f"token {token}"}
    data = {"name": repo_name, "private": private}
    r = requests.post(url, json=data, headers=headers)
    return r.status_code == 201

def list_repos(token):
    """Ambil semua repo milik user dari GitHub (support pagination)."""
    url     = "https://api.github.com/user/repos"
    headers = {"Authorization": f"token {token}"}
    repos   = []
    page    = 1
    while True:
        r = requests.get(url, headers=headers, params={
            "per_page": 100, "page": page,
            "affiliation": "owner", "sort": "updated"
        })
        if r.status_code != 200:
            return None          # token tidak valid / network error
        data = r.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos
