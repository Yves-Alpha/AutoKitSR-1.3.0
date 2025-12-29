# --- Bootstrap sans venv : PYTHONPATH local + PATH Homebrew ---
import os, sys
from pathlib import Path
APP_NAME = "AutoKitSR"
SUPPORT_DIR = Path.home() / "Library" / "Application Support" / APP_NAME
SITE_DIR = SUPPORT_DIR / "site-packages"
SUPPORT_DIR.mkdir(parents=True, exist_ok=True)
SITE_DIR.mkdir(parents=True, exist_ok=True)
if str(SITE_DIR) not in sys.path:
    sys.path.insert(0, str(SITE_DIR))
os.environ["PATH"] = "/opt/homebrew/bin:/usr/local/bin:" + os.environ.get("PATH", "")

import io
import re
import unicodedata
from pathlib import Path
import streamlit as st
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, BooleanObject, DictionaryObject
# OCR and image imports
from pdf2image import convert_from_bytes
import pytesseract
import shutil
import os
import sys
import base64

# Charger le CSS externe depuis assets
css_path = Path(__file__).resolve().parent.parent / "assets" / "style.css"
if css_path.exists():
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Charger l'image de fond et la convertir en base64
LOCAL_ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
banner_image_path = LOCAL_ASSETS_DIR / "bg-title.jpeg"
banner_data_uri = ""
if banner_image_path.exists():
    try:
        with open(banner_image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
            banner_data_uri = f"data:image/jpeg;base64,{image_data}"
    except Exception:
        pass

# Injecter le CSS avec l'image de fond encodée
if banner_data_uri:
    banner_css = f"""
    .banner {{
        background-image: url("{banner_data_uri}") !important;
    }}
    """
    st.markdown(f"<style>{banner_css}</style>", unsafe_allow_html=True)
# Find tesseract binary (add /usr/bin for Streamlit Cloud/Debian)
tesseract_path = shutil.which("tesseract")
if not tesseract_path:
    candidates = ["/usr/bin/tesseract", "/opt/homebrew/bin/tesseract", "/usr/local/bin/tesseract"]
    for candidate in candidates:
        if os.path.exists(candidate):
            tesseract_path = candidate
            break
if not tesseract_path:
    raise EnvironmentError(
        "Tesseract binary not found. Please install Tesseract OCR and ensure it is on your PATH or located at /opt/homebrew/bin/tesseract or /usr/local/bin/tesseract."
    )
pytesseract.pytesseract.tesseract_cmd = tesseract_path

# TESSDATA (langues) : tente de localiser fra.traineddata automatiquement
tessdata_candidates = []
tess_bin = Path(tesseract_path).resolve()
tessdata_candidates.append(tess_bin.parent.parent / "share" / "tessdata")
tessdata_candidates.append(tess_bin.parent / "tessdata")
# Add common tessdata paths (Homebrew, Debian/Ubuntu, local override)
tessdata_candidates += [
    Path("/opt/homebrew/share/tessdata"),
    Path("/usr/local/share/tessdata"),
    Path("/usr/share/tessdata"),
    Path("/usr/share/tesseract-ocr/4.00/tessdata"),
    Path("/usr/share/tesseract-ocr/5/tessdata"),
    SUPPORT_DIR / "tessdata",  # emplacement perso éventuel
]
TESSDATA_DIR = None
for cand in tessdata_candidates:
    if (cand / "fra.traineddata").is_file():
        TESSDATA_DIR = cand
        break
if TESSDATA_DIR:
    os.environ["TESSDATA_PREFIX"] = str(TESSDATA_DIR)
else:
    st.warning(
        "Langue Tesseract 'fra' introuvable. Installe-la avec `brew install tesseract-lang` "
        "ou dépose fra.traineddata dans /opt/homebrew/share/tessdata."
    )
OCR_LANG = "fra" if TESSDATA_DIR else "eng"

pdfinfo_path = shutil.which("pdfinfo")
POPPLER_PATH = str(Path(pdfinfo_path).parent) if pdfinfo_path else "/opt/homebrew/bin"

# Définir correctement le répertoire des templates selon l'environnement
if getattr(sys, "frozen", False):
    # Environnement packagé (bundle .app)
    TEMPLATE_DIR = Path(sys.executable).resolve().parent / "templates"
else:
    # Environnement développement
    TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"

HOME_ASSETS_DIR = Path.home() / "AutoKitSR"

def normalize_text(s: str) -> str:
    if s is None:
        return ""
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().upper()

def normalize_name_for_match(s: str) -> str:
    """Normalize file/keyword names for matching (remove spaces, punctuation, accents)."""
    if s is None:
        return ""
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", s).lower())

def ocr_page(page):
    # Convert PdfPage to image using pdf2image and run pytesseract
    buffer = io.BytesIO()
    writer = PdfWriter()
    writer.add_page(page)
    writer.write(buffer)
    buffer.seek(0)
    images = convert_from_bytes(buffer.getvalue(), dpi=200, poppler_path=POPPLER_PATH)
    text = ""
    for img in images:
        text += pytesseract.image_to_string(img, lang=OCR_LANG, config="--psm 6")
    return text

st.set_page_config(
    page_title="Kit SR Auto",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={"About": "Kit Stop Rayons - Spécial Francap"},
    page_icon="📦"
)

with st.container():
    st.markdown(
        """
        <div class="banner">
            <h1>Kit Stop Rayons automatisé</h1>
            <p>Spécial Francap</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with st.container(border=True):
    st.markdown("### Dates de l’opération")
    st.caption("Saisis les dates au format **jj/mm/aa** (ex : 03/09/25).")
    cols = st.columns(2)
    start_date = cols[0].text_input("Date de début (jj/mm/aa)", key="start_date")
    end_date = cols[1].text_input("Date de fin (jj/mm/aa)", key="end_date")

with st.container(border=True):
    st.markdown("### Numéro d’OP")
    st.caption("Il est extrait du nom du PDF si possible. Tu peux aussi le renseigner ici.")
    code_op_input = st.text_input("Numéro OP (4 chiffres)", key="code_op_manual")

def _norm_date(s: str):
    import re as _re
    m = _re.match(r"^\s*(\d{1,2})/(\d{1,2})/(\d{2})\s*$", s or "")
    if not m:
        return None
    d, mth, yy = m.groups()
    return f"{int(d):02d}/{int(mth):02d}/{yy}"

dates_op = ""
if start_date and end_date:
    sd = _norm_date(start_date)
    ed = _norm_date(end_date)
    if sd and ed:
        dates_op = f"Du {sd} au {ed}"
    elif start_date or end_date:
        st.error("Format de date invalide. Utiliser le format jj/mm/aa (ex : 03/09/25).")

with st.container(border=True):
    st.markdown("### Choisir un le format de magasin")
    filter_choice = st.radio(
        "Formats disponibles :",
        ["SUPERMARCHE", "EXPRESS", "MARKET", "PANIER SYMPA", "MARCHE MINUT"],
        horizontal=True,
    )

with st.container(border=True):
    st.markdown("### Déposer le PDF HD des SR à filtrer")
    uploaded_file = st.file_uploader("Fichier PDF du catalogue", type=["pdf"])

with st.container(border=True):
    st.markdown("### Choisir l'affilié")
    group_choice = st.radio(
        "Affiliés disponibles :",
        ["Ségurel", "Codifrance", "DDS Aldouest", "DEGRENNE"],
        horizontal=True,
    )

template_path = None

generate_clicked = st.button("Générer le PDF")

if generate_clicked:
    # validations obligatoires
    if not uploaded_file:
        st.error("Veuillez déposer le PDF HD des SR à filtrer avant de générer.")
        st.stop()
    # normalisation des dates
    sd = _norm_date(start_date)
    ed = _norm_date(end_date)
    if not (sd and ed):
        st.error("Veuillez renseigner des dates valides au format jj/mm/aa (ex : 03/09/25).")
        st.stop()
    dates_op = f"Du {sd} au {ed}"

    file_name = uploaded_file.name
    data = uploaded_file.read()
    reader = PdfReader(io.BytesIO(data))
    writer = PdfWriter()
    count = 0

    keyword = filter_choice.upper()
    detection_keyword = {"PANIER SYMPA": "MARKET", "MARCHE MINUT": "MARKET"}.get(
        keyword, keyword
    )

    # Try to extract code_op from filename if not manually entered or invalid
    if code_op_input and re.match(r"^\d{4}$", code_op_input.strip()):
        code_op = code_op_input.strip()
    else:
        code_op_match = re.match(r"(\d{4})", Path(file_name).stem)
        if code_op_match:
            code_op = code_op_match.group(1)
        else:
            code_op = None

    if code_op is None:
        st.error("Le numéro OP doit être un code de 4 chiffres. Veuillez le saisir manuellement.")
        st.stop()

    # Find template file based on group_choice and filter_choice
    group_dir = TEMPLATE_DIR / group_choice
    if not group_dir.exists():
        st.error(f"Le dossier de modèles pour {group_choice} est introuvable.")
        st.stop()
    keyword_norm = normalize_name_for_match(filter_choice)
    alias_terms = {
        "supermarche": ["super"],        # fichiers nommés *SUPER.pdf
        "paniersympa": ["paniersympa"],  # fichiers sans espace
        "marcheminut": ["marcheminut"],  # fichiers sans espace
    }
    search_terms = [keyword_norm] + alias_terms.get(keyword_norm, [])
    matches = [
        p for p in group_dir.glob("*.pdf")
        if any(term in normalize_name_for_match(p.name) for term in search_terms)
    ]
    if not matches:
        # Fallback : prend le premier PDF disponible pour l'affilié (cas d'un template unique)
        fallback = sorted(group_dir.glob("*.pdf"))
        if fallback:
            template_path = fallback[0]
            st.info(
                f"Aucun modèle spécifique pour {filter_choice}. Utilisation du modèle par défaut : {template_path.name}"
            )
        else:
            st.error(f"Aucun modèle trouvé pour {group_choice} (aucun PDF dans {group_dir}).")
            st.stop()
    else:
        template_path = matches[0]

    progress_bar = st.progress(0)
    total_pages = len(reader.pages)

    for i, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "")
        norm_keyword = normalize_text(detection_keyword)
        norm_text = normalize_text(text)
        if norm_keyword not in norm_text:
            # Try OCR if keyword not found
            text = ocr_page(page)
            norm_text = normalize_text(text)
        if norm_keyword in norm_text:
            writer.add_page(page)
            count += 1
        # Use percentage to improve compatibility across Streamlit versions
        progress_bar.progress(int(i * 100 / total_pages))

    if count > 0:

        nb_sr = str(count)

        metadata = {}
        title = st.text_input("Titre", value=Path(file_name).stem)
        author = st.text_input("Auteur", value="")
        if title:
            metadata["/Title"] = title
        if author:
            metadata["/Author"] = author

        suffix_map = {
            "SUPERMARCHE": "-SUPER",
            "EXPRESS": "-EXPRESS",
            "MARKET": "-MARKET",
            "PANIER SYMPA": "-PANIERSYMPA",
            "MARCHE MINUT": "-MARCHEMINUT",
        }
        suffix = suffix_map.get(keyword, f"-{keyword}")
        out_name = Path(file_name).stem + suffix + ".pdf"

        # Générer le PDF filtré dans un buffer temporaire
        filtered_buffer = io.BytesIO()
        filtered_writer = PdfWriter()
        for i, page in enumerate(writer.pages):
            filtered_writer.add_page(page)
        if metadata:
            filtered_writer.add_metadata(metadata)
        filtered_writer.write(filtered_buffer)
        filtered_buffer.seek(0)

        # Charger le PDF filtré
        filtered_reader = PdfReader(filtered_buffer)

        if not template_path.exists():
            st.error(f"Le modèle de résumé sélectionné '{template_path.name}' est introuvable.")
            st.stop()

        resume_reader = PdfReader(str(template_path))

        from pypdf import PdfReader as PypdfReader, PdfWriter as PypdfWriter

        def _set_need_appearances(w):
            # Assure que /AcroForm existe et que /NeedAppearances=True
            catalog = w._root_object
            if NameObject("/AcroForm") not in catalog:
                catalog[NameObject("/AcroForm")] = DictionaryObject()
            acro = catalog[NameObject("/AcroForm")]
            # Résout l’objet indirect si nécessaire
            try:
                acro = acro.get_object()
            except Exception:
                pass
            if acro is None:
                acro = DictionaryObject()
                catalog[NameObject("/AcroForm")] = acro
            acro[NameObject("/NeedAppearances")] = BooleanObject(True)

        # Détecter des champs de formulaire sur le résumé
        fields = None
        try:
            fields = resume_reader.get_fields()
        except Exception:
            fields = None

        if fields:
            # Remplir les champs si présents
            form_writer = PypdfWriter()
            # Cloner le document pour conserver l’AcroForm et les champs
            form_writer.clone_document_from_reader(resume_reader)
            try:
                form_writer.update_page_form_field_values(
                    form_writer.pages[0],
                    {
                        "CodeOP": code_op,
                        "Date1_af_date1": sd,
                        "Date2_af_date2": ed,
                        "NombredeSR": nb_sr,
                    }
                )
                _set_need_appearances(form_writer)
            except Exception:
                # Inform user if fields exist but could not be filled (names/permissions)
                st.info(
                    "Impossible de remplir les champs du modèle (noms ou permissions). "
                    "Le PDF sera généré sans remplissage des champs."
                )
            resume_buf = io.BytesIO()
            form_writer.write(resume_buf)
            resume_buf.seek(0)
            resume_reader = PypdfReader(resume_buf)

            merged_writer = PypdfWriter()
            # Ajouter le résumé rempli en premier
            for p in resume_reader.pages:
                merged_writer.add_page(p)
        else:
            # Fallback : overlay reportlab sur la 1ère page du résumé
            from reportlab.pdfgen import canvas
            from reportlab.lib.units import mm

            first_resume_page = resume_reader.pages[0]
            mediabox = first_resume_page.mediabox
            page_width = float(mediabox.width)
            page_height = float(mediabox.height)

            overlay_buffer = io.BytesIO()
            c = canvas.Canvas(overlay_buffer, pagesize=(page_width, page_height))
            x0 = 30 * mm
            y0 = page_height - 40 * mm
            c.setFont("Helvetica-Bold", 13)
            c.drawString(x0, y0, f"Code OP: {code_op}")
            c.setFont("Helvetica", 12)
            c.drawString(x0, y0 - 15, f"Dates de l’opération: Du {sd} au {ed}")
            c.drawString(x0, y0 - 30, f"Nombre de SR: {nb_sr}")
            c.save()
            overlay_buffer.seek(0)

            overlay_pdf = PypdfReader(overlay_buffer)
            overlay_page = overlay_pdf.pages[0]

            merged_writer = PypdfWriter()
            # Fusionner overlay sur la première page du résumé
            base_page = resume_reader.pages[0]
            base_page.merge_page(overlay_page)
            merged_writer.add_page(base_page)
            # Ajouter les autres pages du résumé (s'il y en a)
            for i in range(1, len(resume_reader.pages)):
                merged_writer.add_page(resume_reader.pages[i])

        # Ajouter les pages filtrées
        for i in range(len(filtered_reader.pages)):
            merged_writer.add_page(filtered_reader.pages[i])

        # Ajouter les métadonnées
        if metadata:
            merged_writer.add_metadata(metadata)

        buffer = io.BytesIO()
        merged_writer.write(buffer)
        buffer.seek(0)

        total_pages_final = count + len(resume_reader.pages)

        st.success(f"PDF final généré avec {total_pages_final} page(s) : {len(resume_reader.pages)} page(s) du résumé, {count} page(s) extraites.")
        st.download_button("Télécharger le PDF final", buffer, file_name=out_name, mime="application/pdf")
    else:
        st.warning(f"Aucune page ne contient le mot '{filter_choice}'")
