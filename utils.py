import subprocess

def run(cmd, allow_fail=False):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # "nothing to commit" bukan error sejati
        if "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
            print("ℹ️  Tidak ada perubahan baru untuk di-commit.")
            return True
        if not allow_fail:
            out = result.stdout.strip() or result.stderr.strip()
            if out:
                print(out)
            print("❌ Command gagal:", " ".join(cmd))
        return False
    # Tampilkan output jika ada
    if result.stdout.strip():
        print(result.stdout.strip())
    return True

def ask(msg):
    return input(f"{msg}: ").strip()
