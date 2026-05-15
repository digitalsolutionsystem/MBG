from utils import run, ask
from github_api import create_repo
from config import CONFIG
from token_store import get_token, get_username, save_credentials, clear_credentials
import os
import sys
import subprocess
import time

# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

last_log = {"msg": "", "status": ""}  # status: ok | fail | info

def log(msg, status="info"):
    last_log["msg"] = msg
    last_log["status"] = status

def clear():
    os.system("clear")

def get_current_branch():
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True
    )
    branch = result.stdout.strip()
    return branch if branch and branch != "HEAD" else None

def has_commits():
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True, text=True
    )
    return result.returncode == 0

def set_git_credentials(token, username):
    cred = f"protocol=https\nhost=github.com\nusername={username}\npassword={token}\n"
    subprocess.run(
        ["git", "credential", "approve"],
        input=cred, text=True, capture_output=True
    )

# ──────────────────────────────────────────────
# MENU DISPLAY
# ──────────────────────────────────────────────

def menu():
    clear()

    token_status = "✅ Tersimpan" if get_token() else "❌ Belum diset"
    user_status  = get_username() or "❌ Belum diset"
    branch       = get_current_branch() or "-"
    committed    = "✅ Ada" if has_commits() else "❌ Belum ada"

    # Tampilkan log aksi terakhir
    status_icons = {"ok": "✅", "fail": "❌", "info": "ℹ️ "}
    icon = status_icons.get(last_log["status"], "ℹ️ ")
    log_line = f"{icon} {last_log['msg']}" if last_log["msg"] else "—"

    print(f"""\
{CONFIG['app_name']} v{CONFIG['version']}
══════════════════════════════
🔑 Token  : {token_status}
👤 User   : {user_status}
🌿 Branch : {branch}
📦 Commit : {committed}
──────────────────────────────
📋 Log    : {log_line}
══════════════════════════════
1. Init Git
2. Commit
3. Push
4. Create GitHub Repo + Push
5. Set / Ganti Kredensial
6. Hapus Kredensial
7. Exit
──────────────────────────────
💡 mbg init | commit | push | create
""")

# ──────────────────────────────────────────────
# CORE FUNCTIONS
# ──────────────────────────────────────────────

def init_git():
    if not os.path.exists(".git"):
        run(["git", "init"])
    run(["git", "add", "."])
    log("Git diinisialisasi & file di-stage", "ok")

def commit(msg=None):
    if not msg:
        msg = ask("Pesan commit")
    run(["git", "add", "."])
    result = subprocess.run(
        ["git", "commit", "-m", msg],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        if "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
            log("Tidak ada perubahan baru untuk di-commit", "info")
        else:
            log("Commit gagal", "fail")
    else:
        log(f"Commit berhasil: \"{msg}\"", "ok")

def push(branch=None):
    if not branch:
        branch = get_current_branch() or "main"
    result = subprocess.run(
        ["git", "push", "-u", "origin", branch],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        err = result.stderr.strip()
        log(f"Push gagal → {err.splitlines()[-1] if err else 'unknown'}", "fail")
    else:
        log(f"Push berhasil ke branch '{branch}'", "ok")

def setup_credentials():
    clear()
    print("🔑 Setup Kredensial GitHub")
    print("─" * 32)
    token    = ask("GitHub Token")
    username = ask("Username GitHub")
    if token and username:
        save_credentials(token, username)
        set_git_credentials(token, username)
        log(f"Kredensial disimpan untuk '{username}'", "ok")
    else:
        log("Token/username tidak boleh kosong", "fail")

def _ensure_credentials():
    token    = get_token()
    username = get_username()
    if not token or not username:
        setup_credentials()
        token    = get_token()
        username = get_username()
    return token, username

def do_push(branch=None):
    if not os.path.exists(".git"):
        log("Belum ada git repo — jalankan Init Git dulu", "fail")
        return
    if not has_commits():
        log("Belum ada commit — lakukan Commit dulu", "fail")
        return
    push(branch)

def create_repo_and_push(branch=None):
    if not os.path.exists(".git"):
        log("Belum ada git repo — jalankan Init Git dulu", "fail")
        return
    if not has_commits():
        log("Belum ada commit — lakukan Commit dulu", "fail")
        return

    token, username = _ensure_credentials()
    if not token or not username:
        return

    set_git_credentials(token, username)

    clear()
    print("🚀 Create GitHub Repo + Push")
    print("─" * 32)
    repo    = ask("Nama repo")
    private = ask("Private? (y/n)").lower() == "y"

    print("⏳ Membuat repo di GitHub...")
    if create_repo(token, repo, private):
        remote_url = f"https://github.com/{username}/{repo}.git"
        result = subprocess.run(["git", "remote"], capture_output=True, text=True)
        if "origin" in result.stdout:
            subprocess.run(["git", "remote", "set-url", "origin", remote_url])
        else:
            subprocess.run(["git", "remote", "add", "origin", remote_url])

        print(f"⏳ Push ke {remote_url}...")
        push(branch)
        if last_log["status"] == "ok":
            log(f"Repo '{repo}' dibuat & berhasil di-push", "ok")
    else:
        log(f"Gagal membuat repo '{repo}' — sudah ada atau token tidak valid", "fail")

# ──────────────────────────────────────────────
# INTERACTIVE LOOP
# ──────────────────────────────────────────────

def interactive():
    while True:
        menu()
        choice = ask("Pilih menu")

        if   choice == "1": init_git()
        elif choice == "2": commit()
        elif choice == "3": do_push()
        elif choice == "4": create_repo_and_push()
        elif choice == "5": setup_credentials()
        elif choice == "6":
            clear_credentials()
            log("Kredensial dihapus", "info")
        elif choice == "7":
            clear()
            print("👋 Sampai jumpa!")
            break
        else:
            log(f"Pilihan '{choice}' tidak valid", "fail")

# ──────────────────────────────────────────────
# CLI ENTRY POINT
# ──────────────────────────────────────────────

HELP = f"""
{CONFIG['app_name']} v{CONFIG['version']} — Git & GitHub CLI Tool
================================================
Penggunaan:
  mbg                        Buka menu interaktif
  mbg init                   Init git + git add .
  mbg commit "pesan"         Commit dengan pesan
  mbg push [branch]          Push ke branch (auto-deteksi)
  mbg create [branch]        Buat repo GitHub baru lalu push
  mbg set                    Set / ganti token & username
  mbg clear                  Hapus kredensial tersimpan
  mbg help                   Tampilkan bantuan ini
"""

def main():
    args = sys.argv[1:]

    if not args:
        interactive()
        return

    cmd = args[0].lower()

    if cmd == "init":
        init_git(); print(last_log["msg"])
    elif cmd == "commit":
        commit(args[1] if len(args) > 1 else None); print(last_log["msg"])
    elif cmd == "push":
        do_push(args[1] if len(args) > 1 else None); print(last_log["msg"])
    elif cmd == "create":
        create_repo_and_push(args[1] if len(args) > 1 else None)
    elif cmd == "set":
        setup_credentials()
    elif cmd == "clear":
        clear_credentials()
    elif cmd in ("help", "--help", "-h"):
        print(HELP)
    else:
        print(f"❌ Perintah tidak dikenal: '{cmd}'")
        print(HELP)

if __name__ == "__main__":
    main()
