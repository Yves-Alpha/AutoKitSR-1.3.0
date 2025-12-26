#!/bin/zsh
set -euo pipefail

# Installation utilisateur (sans venv embarqué) : deps dans ~/Library/Application Support/AutoKitSR/site-packages

export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

APP_NAME="AutoKitSR"
SUPPORT_DIR="$HOME/Library/Application Support/$APP_NAME"
SITE_PACKAGES="$SUPPORT_DIR/site-packages"
REQS=("streamlit" "pypdf" "pdf2image" "pytesseract" "Pillow" "reportlab")

echo "=== Installation AutoKitSR ==="

# Vérifie Homebrew
if ! command -v brew >/dev/null 2>&1; then
  echo "⚠️ Homebrew n'est pas installé. Installe-le : https://brew.sh/"
  exit 1
fi

# Dépendances natives
if ! command -v pdftoppm >/dev/null 2>&1; then
  echo "• Installation Poppler (pdftoppm)…"
  brew install poppler
fi
if ! command -v tesseract >/dev/null 2>&1; then
  echo "• Installation Tesseract…"
  brew install tesseract
fi

mkdir -p "$SITE_PACKAGES"

# Choix python
PY_BIN="${PYTHON:-}"
if [ -z "$PY_BIN" ]; then
  for cand in /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 /Library/Frameworks/Python.framework/Versions/3.11/bin/python3 /opt/homebrew/bin/python3 /usr/local/bin/python3; do
    if [ -x "$cand" ]; then PY_BIN="$cand"; break; fi
  done
fi
if [ -z "$PY_BIN" ]; then
  PY_BIN="$(command -v python3 || true)"
fi
if [ -z "$PY_BIN" ]; then
  echo "Python 3 introuvable. Installe Python 3 (>=3.11) puis relance." >&2
  exit 1
fi

echo "• Python utilisé : $PY_BIN"
echo "• Installation des dépendances Python dans $SITE_PACKAGES …"
"$PY_BIN" -m pip install --upgrade --no-warn-script-location --target "$SITE_PACKAGES" "${REQS[@]}"

echo "✅ Installation terminée. Lancez l'app avec :"
echo "   python3 \"$(cd "$(dirname "$0")/.." && pwd)/launch.py\""
