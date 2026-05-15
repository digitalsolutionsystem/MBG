#!/bin/bash
set -e

APP_NAME="mbg"
INSTALL_DIR="/opt/mbg"
VENV_DIR="$INSTALL_DIR/venv"
BIN_PATH="/usr/local/bin/mbg"

echo "📦 Installing M.B.G v2.0.0..."

# Cek Python3
if ! command -v python3 >/dev/null; then
  echo "❌ Python3 belum terinstall. Jalankan: sudo pacman -S python"
  exit 1
fi

# Buat direktori instalasi
sudo mkdir -p "$INSTALL_DIR"

# Salin file aplikasi
sudo cp mbg.py utils.py github_api.py config.py token_store.py requirements.txt "$INSTALL_DIR"

# Buat virtual environment
echo "🐍 Membuat virtual environment..."
sudo python3 -m venv "$VENV_DIR"

# Install dependency ke dalam venv
echo "📥 Menginstall dependency..."
sudo "$VENV_DIR/bin/pip" install --quiet -r "$INSTALL_DIR/requirements.txt"

# Buat launcher script
sudo tee "$BIN_PATH" > /dev/null <<LAUNCHER
#!/bin/bash
exec "$VENV_DIR/bin/python" "$INSTALL_DIR/mbg.py" "\$@"
LAUNCHER

sudo chmod +x "$BIN_PATH"

echo ""
echo "✅ Instalasi selesai! Jalankan: mbg"
