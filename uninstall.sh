#!/bin/bash
set -e

INSTALL_DIR="/opt/mbg"
BIN_PATH="/usr/local/bin/mbg"
CONFIG_DIR="$HOME/.mbg"

echo "🗑️  Uninstall M.B.G..."

# Hapus binary launcher
if [ -f "$BIN_PATH" ]; then
  sudo rm -f "$BIN_PATH"
  echo "✅ Hapus $BIN_PATH"
fi

# Hapus direktori instalasi (termasuk venv)
if [ -d "$INSTALL_DIR" ]; then
  sudo rm -rf "$INSTALL_DIR"
  echo "✅ Hapus $INSTALL_DIR"
fi

# Tanya apakah ingin hapus config/token juga
if [ -d "$CONFIG_DIR" ]; then
  read -rp "❓ Hapus juga kredensial tersimpan (~/.mbg)? (y/n): " answer
  if [[ "$answer" == "y" || "$answer" == "Y" ]]; then
    rm -rf "$CONFIG_DIR"
    echo "✅ Hapus $CONFIG_DIR"
  else
    echo "⏩ Kredensial dipertahankan di $CONFIG_DIR"
  fi
fi

echo ""
echo "✅ M.B.G berhasil diuninstall."
