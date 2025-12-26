# AutoKitSR (BETA 1.3.0) – Installation & lancement

## Prérequis (macOS)
- Python 3 (>= 3.11) présent dans le PATH (`python3 --version`). Si besoin : `brew install python`.
- Poppler (pdftoppm) : `brew install poppler`
- Tesseract : `brew install tesseract`

## Lancement via l’app Platypus
1) Construis l’app avec le profil `AutoKitSR.platypus` (script `launch.py`).
2) Lance `AutoKitSR.app` :
   - installe automatiquement les dépendances Python (`streamlit`, `pypdf`, `pdf2image`, `pytesseract`, `Pillow`, `reportlab`) dans `~/Library/Application Support/AutoKitSR/site-packages`
   - vérifie la présence de Poppler et Tesseract (abort si manquants)
   - démarre Streamlit sur `http://localhost:8501`

## Dépannage
- Poppler/Tesseract manquants : `brew install poppler tesseract`
- Python introuvable : `brew install python`
- Réinstaller proprement les deps Python : supprimer `~/Library/Application Support/AutoKitSR/site-packages` puis relancer l’app (les modules seront réinstallés).

## Lanceur CLI de secours (avec checks guidés)
Depuis le dossier `AutoKitSR 1.3.0` :
```bash
chmod +x install/launch_autokitsr.sh
./install/launch_autokitsr.sh
```
Ce script :
- vérifie Homebrew, Python >= 3.11, Poppler et Tesseract ; affiche la commande `brew install ...` si manquants
- installe les dépendances Python dans `~/Library/Application Support/AutoKitSR/site-packages` si besoin
- démarre Streamlit sur le port 8501 (ou le prochain disponible si 8501 est occupé)

## Déploiement Streamlit Cloud
1. Fichiers à pousser : `streamlit_app.py`, `app/` (code UI), `assets/`, `templates/`, `requirements.txt`, `packages.txt`, `README-AutoKitSR.md`. Évite de pousser `venv/` ou des .app/archives (le `.gitignore` les filtre).
2. Sur Streamlit Cloud : **New app** → choisis le repo/branche → indique `streamlit_app.py` comme fichier principal.
3. `requirements.txt` installe les libs Python (streamlit, pypdf, pdf2image, pytesseract, Pillow, reportlab).
4. `packages.txt` installe les binaires système : `poppler-utils` (pdftoppm) et `tesseract-ocr` + `tesseract-ocr-fra` pour la langue française.
5. Test local rapide (hors app Platypus) :
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   streamlit run streamlit_app.py
   ```
