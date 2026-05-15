import json
import os
import stat

CONFIG_DIR = os.path.expanduser("~/.mbg")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

def _load():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def _save(data):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)
    os.chmod(CONFIG_FILE, stat.S_IRUSR | stat.S_IWUSR)

def get_token():
    return _load().get("github_token")

def get_username():
    return _load().get("github_username")

def save_credentials(token, username):
    data = _load()
    data["github_token"] = token
    data["github_username"] = username
    _save(data)
    print(f"✅ Kredensial disimpan di {CONFIG_FILE}")

def clear_credentials():
    data = _load()
    data.pop("github_token", None)
    data.pop("github_username", None)
    _save(data)
    print("🗑️  Kredensial dihapus.")
