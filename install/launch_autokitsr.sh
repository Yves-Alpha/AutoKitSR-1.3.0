#!/usr/bin/env bash
set -euo pipefail

# Lance AutoKitSR en vérifiant les prérequis et en indiquant les commandes d’installation manquantes.

APP_NAME="AutoKitSR"
SUPPORT_DIR="$HOME/Library/Application Support/$APP_NAME"
SITE_PACKAGES="$SUPPORT_DIR/site-packages"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
# Si on est dans le .app, les ressources sont sous Resources/
if [[ -f "$ROOT_DIR/Resources/app/main.py" ]]; then
  APP_ROOT="$ROOT_DIR/Resources"
else
  APP_ROOT="$ROOT_DIR"
fi
APP_PATH="$APP_ROOT/app/main.py"
DEFAULT_PORT="${PORT:-8501}"

echo "=== Lanceur AutoKitSR (checks & aide installation) ==="

# S'assurer que Homebrew (Intel/Apple Silicon) est dans le PATH
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

# 1) Homebrew
if ! command -v brew >/dev/null 2>&1; then
  echo "❌ Homebrew non détecté."
  echo "   Installe-le avec : /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
  exit 1
fi

# 2) Python 3.11+
PY_BIN="${PYTHON:-$(command -v python3 || true)}"
if [[ -z "$PY_BIN" ]]; then
  echo "❌ python3 introuvable. Installe Python 3 (>=3.11), ex : brew install python@3.13"
  exit 1
fi
if ! "$PY_BIN" - <<'PY'
import sys
major, minor = sys.version_info[:2]
sys.exit(0 if (major > 3 or (major == 3 and minor >= 11)) else 1)
PY
then
  echo "❌ Version Python insuffisante ($("$PY_BIN" --version 2>&1))."
  echo "   Installe Python 3.11+ (ex : brew install python@3.13) puis relance."
  exit 1
fi
echo "• Python utilisé : $("$PY_BIN" --version 2>&1)"

# 3) Binaries poppler / tesseract
missing_bins=()
if ! command -v pdftoppm >/dev/null 2>&1; then
  missing_bins+=("poppler")
fi
if ! command -v tesseract >/dev/null 2>&1; then
  missing_bins+=("tesseract")
fi
if [[ ${#missing_bins[@]} -gt 0 ]]; then
  echo "❌ Dépendances natives manquantes : ${missing_bins[*]}"
  echo "   Installe-les avec : brew install ${missing_bins[*]}"
  exit 1
fi

# 4) Dépendances Python (install dans Application Support)
mkdir -p "$SITE_PACKAGES"
export PYTHONPATH="$SITE_PACKAGES${PYTHONPATH:+:$PYTHONPATH}"

missing_py="$("$PY_BIN" - <<'PY'
import importlib.util, json
req = ["streamlit", "pypdf", "pdf2image", "pytesseract", "Pillow", "reportlab"]
missing = [m for m in req if importlib.util.find_spec(m) is None]
print(json.dumps(missing))
PY
)"
if [[ "$missing_py" != "[]" ]]; then
  echo "• Installation des modules Python manquants dans '$SITE_PACKAGES'..."
  "$PY_BIN" -m pip install --upgrade --no-warn-script-location --target "$SITE_PACKAGES" streamlit pypdf pdf2image pytesseract Pillow reportlab
fi

# 5) Choix du port : on prend le premier disponible à partir de DEFAULT_PORT
PORT="$("$PY_BIN" - <<PY
import socket
start = int("${DEFAULT_PORT}")
def free(p):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(("127.0.0.1", p))
        except OSError:
            return False
    return True
chosen = None
for port in range(start, start + 50):
    if free(port):
        chosen = port
        break
print(chosen or start)
PY
)"
if [[ "$PORT" != "$DEFAULT_PORT" ]]; then
  echo "ℹ️ Port $DEFAULT_PORT indisponible, utilisation du port $PORT."
fi

echo "• Lancement de l'UI Streamlit..."
exec "$PY_BIN" -m streamlit run "$APP_PATH" \
  --server.port "$PORT" \
  --server.address "127.0.0.1" \
  --server.headless false \
  --server.fileWatcherType none \
  --browser.gatherUsageStats false
