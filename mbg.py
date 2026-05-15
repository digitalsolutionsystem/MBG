from utils import run, ask
from github_api import create_repo, list_repos
from config import CONFIG
from token_store import get_token, get_username, save_credentials, clear_credentials
import os
import sys
import subprocess

# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

last_log = {"msg": "", "status": ""}

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

def is_git_repo():
    result = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        capture_output=True, text=True
    )
    return result.returncode == 0

def has_commits():
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True, text=True
    )
    return result.returncode == 0

def get_remote_url():
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        capture_output=True, text=True
    )
    return result.stdout.strip() if result.returncode == 0 else None

def set_git_credentials(token, username):
    cred = f"protocol=https\nhost=github.com\nusername={username}\npassword={token}\n"
    subprocess.run(["git", "credential", "approve"],
                   input=cred, text=True, capture_output=True)

def scan_git_projects(search_dirs=None):
    """Cari semua folder yang punya .git di direktori umum."""
    if search_dirs is None:
        home = os.path.expanduser("~")
        search_dirs = [
            home,
            os.path.join(home, "projects"),
            os.path.join(home, "dev"),
            os.path.join(home, "code"),
            os.path.join(home, "workspace"),
            "/opt",
        ]

    found = []
    for base in search_dirs:
        if not os.path.isdir(base):
            continue
        try:
            for name in sorted(os.listdir(base)):
                path = os.path.join(base, name)
                if os.path.isdir(path) and os.path.isdir(os.path.join(path, ".git")):
                    # Ambil remote origin-nya
                    r = subprocess.run(
                        ["git", "-C", path, "remote", "get-url", "origin"],
                        capture_output=True, text=True
                    )
                    remote = r.stdout.strip() if r.returncode == 0 else "(no remote)"
                    # Bersihkan token dari URL jika ada
                    if "@github.com" in remote:
                        remote = "https://github.com/" + remote.split("@github.com/")[-1]
                    # Ambil branch aktif
                    b = subprocess.run(
                        ["git", "-C", path, "rev-parse", "--abbrev-ref", "HEAD"],
                        capture_output=True, text=True
                    )
                    branch = b.stdout.strip() if b.returncode == 0 else "?"
                    found.append({
                        "name": name,
                        "path": path,
                        "remote": remote,
                        "branch": branch,
                    })
        except PermissionError:
            continue
    return found

# ──────────────────────────────────────────────
# MENU DISPLAY
# ──────────────────────────────────────────────

def menu():
    clear()
    token_status = "✅ Tersimpan" if get_token() else "❌ Belum diset"
    user_status  = get_username() or "❌ Belum diset"
    branch       = get_current_branch() or "-"
    committed    = "✅ Ada" if has_commits() else "❌ Belum ada"
    remote       = get_remote_url() or "-"
    if "@github.com" in remote:
        remote = "https://github.com/" + remote.split("@github.com/")[-1]

    icons = {"ok": "✅", "fail": "❌", "info": "ℹ️ "}
    icon  = icons.get(last_log["status"], "ℹ️ ")
    log_line = f"{icon} {last_log['msg']}" if last_log["msg"] else "—"

    print(f"""\
{CONFIG['app_name']} v{CONFIG['version']}
══════════════════════════════════════
🔑 Token  : {token_status}
👤 User   : {user_status}
🌿 Branch : {branch}
📦 Commit : {committed}
🔗 Remote : {remote}
──────────────────────────────────────
📋 Log    : {log_line}
══════════════════════════════════════
1. Init Git
2. Commit
3. Push
4. Create GitHub Repo + Push
5. Update Repo (saran project)
6. Set / Ganti Kredensial
7. Hapus Kredensial
8. Exit
──────────────────────────────────────
💡 mbg init | commit | push | create | update
""")

# ──────────────────────────────────────────────
# CORE FUNCTIONS
# ──────────────────────────────────────────────

def init_git():
    if not is_git_repo():
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

def push(branch=None, project_path=None):
    """Push repo. Jika project_path diberikan, push dari folder itu."""
    cwd = project_path or os.getcwd()

    if not branch:
        b = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True
        )
        branch = b.stdout.strip() if b.returncode == 0 else "main"

    token    = get_token()
    username = get_username()

    remote_result = subprocess.run(
        ["git", "-C", cwd, "remote", "get-url", "origin"],
        capture_output=True, text=True
    )
    if remote_result.returncode != 0:
        log("Tidak ada remote origin — jalankan menu 4 dulu", "fail")
        return

    remote_url = remote_result.stdout.strip()
    if token and "github.com" in remote_url:
        if "@github.com" in remote_url:
            remote_url = "https://github.com/" + remote_url.split("@github.com/")[-1]
        auth_url = remote_url.replace("https://", f"https://{token}@")
    else:
        auth_url = remote_url

    result = subprocess.run(
        ["git", "-C", cwd, "push", "-u", auth_url, branch],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        err = result.stderr.strip()
        log(f"Push gagal → {err.splitlines()[-1] if err else 'unknown'}", "fail")
    else:
        log(f"Push berhasil ke branch '{branch}'", "ok")

def _ensure_credentials():
    token    = get_token()
    username = get_username()
    if not token or not username:
        log("Kredensial belum diset — pilih menu 6 dulu", "fail")
        return None, None
    return token, username

def do_push(branch=None):
    if not is_git_repo():
        log("Belum ada git repo — jalankan Init Git dulu", "fail")
        return
    if not has_commits():
        log("Belum ada commit — lakukan Commit dulu", "fail")
        return
    push(branch)

def create_repo_and_push(branch=None):
    if not is_git_repo():
        log("Belum ada git repo — jalankan Init Git dulu", "fail")
        return
    if not has_commits():
        log("Belum ada commit — lakukan Commit dulu", "fail")
        return

    token, username = _ensure_credentials()
    if not token or not username:
        return

    clear()
    print("🚀 Create GitHub Repo + Push")
    print("─" * 38)
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

def update_repo():
    """Push isi folder saat ini ke repo GitHub pilihan user."""
    clear()
    cwd      = os.getcwd()
    cwd_name = os.path.basename(cwd)
    print(f"🔄 Update Repo — {cwd_name}")
    print(f"   📂 {cwd}")
    print("─" * 38)

    token, username = _ensure_credentials()
    if not token or not username:
        return

    # ── 1. Fetch daftar repo GitHub ───────────
    print("⏳ Mengambil daftar repo dari GitHub...", end="\r", flush=True)
    github_repos = list_repos(token)
    if github_repos is None:
        log("Gagal mengambil repo GitHub — cek token / koneksi", "fail")
        return
    if not github_repos:
        log("Tidak ada repo ditemukan di akun GitHub", "fail")
        return
    print(f"✅ {len(github_repos)} repo ditemukan                      \n")

    # ── 2. Tandai repo yang sudah jadi remote CWD ──
    current_remote = get_remote_url() or ""
    if "@github.com" in current_remote:
        current_remote = "https://github.com/" + current_remote.split("@github.com/")[-1]

    # ── 3. Tampilkan list repo ────────────────
    for i, gh in enumerate(github_repos, 1):
        lock       = "🔒" if gh.get("private") else "🔓"
        stars      = f" ⭐{gh['stargazers_count']}" if gh.get("stargazers_count") else ""
        active_tag = " ◀ aktif" if gh["clone_url"].rstrip("/") == current_remote.rstrip("/") or \
                                   gh["clone_url"].rstrip("/.git") in current_remote else ""
        print(f"  {i}. {lock} {gh['full_name']}{stars}{active_tag}")

    print("\n  0. ← Kembali ke menu")
    print("─" * 38)

    choice = ask("Pilih target repo (nomor)")
    if choice == "0":
        return

    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(github_repos):
            log("Nomor tidak valid", "fail")
            return
    except ValueError:
        log("Input harus berupa angka", "fail")
        return

    gh         = github_repos[idx]
    remote_url = f"https://github.com/{gh['full_name']}.git"
    branch     = get_current_branch() or "main"

    clear()
    print(f"🔄 Update → {gh['full_name']}")
    print(f"   📂 {cwd}")
    print(f"   🌿 {branch}")
    print("─" * 38)

    # ── 4. Init git jika belum ────────────────
    if not is_git_repo():
        print("⏳ Init git repo...")
        subprocess.run(["git", "init"], capture_output=True)
        subprocess.run(["git", "checkout", "-b", branch], capture_output=True)

    # ── 5. Set / update remote origin ────────
    auth_url = remote_url.replace("https://", f"https://{token}@")
    remotes  = subprocess.run(["git", "remote"], capture_output=True, text=True).stdout
    if "origin" in remotes:
        subprocess.run(["git", "remote", "set-url", "origin", remote_url], capture_output=True)
    else:
        subprocess.run(["git", "remote", "add", "origin", remote_url], capture_output=True)
    print(f"🔗 Remote → {remote_url}")

    # ── 6. Fetch & sinkron dengan remote DULU ─
    print("⏳ Fetch dari remote...", end="\r", flush=True)
    fetch_result = subprocess.run(
        ["git", "fetch", auth_url, branch],
        capture_output=True, text=True
    )
    if fetch_result.returncode == 0:
        if not has_commits():
            # Fresh repo: arahkan branch ke FETCH_HEAD supaya history nyambung
            subprocess.run(
                ["git", "update-ref", f"refs/heads/{branch}", "FETCH_HEAD"],
                capture_output=True
            )
        else:
            # Repo sudah ada commit: rebase lokal ke atas remote
            rebase_result = subprocess.run(
                ["git", "rebase", "FETCH_HEAD"],
                capture_output=True, text=True
            )
            if rebase_result.returncode != 0:
                subprocess.run(["git", "rebase", "--abort"], capture_output=True)
                err = rebase_result.stderr.strip() or rebase_result.stdout.strip()
                print("\n" + "═" * 38)
                print(f"❌ SYNC GAGAL ke {gh['full_name']}")
                print(f"   ⚠️  {err.splitlines()[-1] if err else 'unknown'}")
                print("   💡 Selesaikan konflik manual lalu coba lagi")
                print("═" * 38)
                log("Sync gagal — selesaikan konflik manual", "fail")
                input("\nTekan Enter untuk kembali ke menu...")
                return
        print("✅ Sync dengan remote selesai      ")
    else:
        # Remote branch belum ada (repo GitHub masih kosong) - lanjut langsung
        print("ℹ️  Remote branch belum ada, lanjut push...   ")

    # ── 7. Cek perubahan & commit ─────────────
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True
    )
    changed_files = status.stdout.strip()
    commit_msg    = None

    if changed_files:
        print(f"\n📝 File berubah:\n{changed_files}\n")
        commit_msg = ask("Pesan commit")
        subprocess.run(["git", "add", "."])
        result = subprocess.run(
            ["git", "commit", "-m", commit_msg],
            capture_output=True, text=True
        )
        if result.returncode != 0 and "nothing to commit" not in result.stdout:
            log("Commit gagal", "fail")
            input("\nTekan Enter untuk kembali ke menu...")
            return
        print(f"✅ Commit: \"{commit_msg}\"")
    else:
        print("ℹ️  Tidak ada perubahan baru, langsung push...\n")

    # ── 8. Push ───────────────────────────────
    push(branch)

    print("\n" + "═" * 38)
    if last_log["status"] == "ok":
        print(f"✅ BERHASIL di-push ke {gh['full_name']}")
        if commit_msg:
            print(f"   💬 Pesan  : \"{commit_msg}\"")
        print(f"   🌿 Branch : {branch}")
        print(f"   📂 Folder : {cwd_name}")
        log(f"'{cwd_name}' berhasil di-push ke {gh['full_name']}", "ok")
    else:
        print(f"❌ PUSH GAGAL ke {gh['full_name']}")
        print(f"   ⚠️  {last_log['msg']}")
    print("═" * 38)
    input("\nTekan Enter untuk kembali ke menu...")

def setup_credentials():
    clear()
    print("🔑 Setup Kredensial GitHub")
    print("─" * 38)
    token    = ask("GitHub Token")
    username = ask("Username GitHub")
    if token and username:
        save_credentials(token, username)
        set_git_credentials(token, username)
        log(f"Kredensial disimpan untuk '{username}'", "ok")
    else:
        log("Token/username tidak boleh kosong", "fail")

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
        elif choice == "5": update_repo()
        elif choice == "6": setup_credentials()
        elif choice == "7":
            clear_credentials()
            log("Kredensial dihapus", "info")
        elif choice == "8":
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
  mbg update                 Update repo (pilih dari daftar project)
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

    if   cmd == "init":   init_git(); print(last_log["msg"])
    elif cmd == "commit": commit(args[1] if len(args) > 1 else None); print(last_log["msg"])
    elif cmd == "push":   do_push(args[1] if len(args) > 1 else None); print(last_log["msg"])
    elif cmd == "create": create_repo_and_push(args[1] if len(args) > 1 else None)
    elif cmd == "update": update_repo()
    elif cmd == "set":    setup_credentials()
    elif cmd == "clear":  clear_credentials()
    elif cmd in ("help", "--help", "-h"): print(HELP)
    else:
        print(f"❌ Perintah tidak dikenal: '{cmd}'")
        print(HELP)

if __name__ == "__main__":
    main()
