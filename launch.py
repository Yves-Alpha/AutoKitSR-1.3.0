#!/usr/bin/env python3
from __future__ import annotations
import subprocess
from pathlib import Path
import sys
import os
import shutil
import importlib.util

# --- App name (fixe) ---
APP_NAME = "AutoKitSR"
DEFAULT_PORT = 8501

base_path = Path(__file__).resolve().parent
app_path = base_path / "app" / "main.py"

# --- Dossier de support (deps Python) ---
SUPPORT_DIR = Path.home() / "Library" / "Application Support" / APP_NAME
SITE_PACKAGES = SUPPORT_DIR / "site-packages"
SITE_PACKAGES.mkdir(parents=True, exist_ok=True)

# PATH / PYTHONPATH
os.environ["PATH"] = "/opt/homebrew/bin:/usr/local/bin:" + os.environ.get("PATH", "")
os.environ["PYTHONPATH"] = str(SITE_PACKAGES) + (":" + os.environ["PYTHONPATH"] if "PYTHONPATH" in os.environ else "")
if str(SITE_PACKAGES) not in sys.path:
    sys.path.insert(0, str(SITE_PACKAGES))


def pick_python() -> Path:
    candidates = [
        Path("/Library/Frameworks/Python.framework/Versions/3.12/bin/python3"),
        Path("/Library/Frameworks/Python.framework/Versions/3.11/bin/python3"),
        Path("/opt/homebrew/bin/python3"),
        Path("/usr/local/bin/python3"),
        Path(sys.executable),
    ]
    for c in candidates:
        if c.exists() and os.access(c, os.X_OK):
            return c
    from shutil import which
    w = which("python3")
    if w:
        return Path(w)
    print("Python 3 est introuvable. Installe Python 3 (>=3.11) via Homebrew ou python.org.")
    sys.exit(1)


def ensure_binaries():
    missing = []
    if not shutil.which("pdftoppm"):
        missing.append("poppler (pdftoppm)")
    if not shutil.which("tesseract"):
        missing.append("tesseract")
    if missing:
        print("Dépendances système manquantes : " + ", ".join(missing))
        print("Installe-les via Homebrew, ex :")
        print("  brew install poppler tesseract")
        sys.exit(1)


def ensure_deps(python_bin: Path) -> None:
    required = ["streamlit", "pypdf", "pdf2image", "pytesseract", "Pillow", "reportlab"]
    missing = [m for m in required if importlib.util.find_spec(m) is None]
    if not missing:
        return
    print(f"Installation des dépendances Python dans {SITE_PACKAGES} ...")
    cmd = [
        str(python_bin),
        "-m",
        "pip",
        "install",
        "--upgrade",
        "--no-warn-script-location",
        "--target",
        str(SITE_PACKAGES),
        *required,
    ]
    subprocess.run(cmd, check=True)


def launch_app(python_bin: Path):
    subprocess.run(["pkill", "-f", "streamlit"], stderr=subprocess.DEVNULL)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SITE_PACKAGES) + (":" + env["PYTHONPATH"] if "PYTHONPATH" in env else "")
    env["PATH"] = "/opt/homebrew/bin:/usr/local/bin:" + env.get("PATH", "")
    cmd = [
        str(python_bin),
        "-m",
        "streamlit",
        "run",
        str(app_path),
        f"--server.port={DEFAULT_PORT}",
        "--server.headless=false",
        "--server.address=127.0.0.1",
        "--server.fileWatcherType=none",
        "--browser.gatherUsageStats=false",
    ]
    subprocess.Popen(cmd, cwd=str(base_path), env=env)


def main():
    ensure_binaries()
    python_bin = pick_python()
    ensure_deps(python_bin)
    launch_app(python_bin)
    print(f"AutoKitSR lancé sur http://localhost:{DEFAULT_PORT}")
    print("Le navigateur devrait s’ouvrir automatiquement (géré par Streamlit).")
    print("Si rien ne s’ouvre, copie/colle cette URL dans ton navigateur.")


if __name__ == "__main__":
    main()
