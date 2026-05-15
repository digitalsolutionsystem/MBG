import requests

def create_repo(token, repo_name, private=False):
    url = "https://api.github.com/user/repos"
    headers = {"Authorization": f"token {token}"}
    data = {"name": repo_name, "private": private}
    r = requests.post(url, json=data, headers=headers)
    return r.status_code == 201
