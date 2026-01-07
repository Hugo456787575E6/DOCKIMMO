import streamlit as st
from openai import OpenAI
import PyPDF2
import io
import base64
from pdf2image import convert_from_bytes
from PIL import Image
from fpdf import FPDF

# 1. Configuration de la page
st.set_page_config(
    page_title="DOCKIMMO | Expert IA",
    page_icon="🏠",
    layout="wide"
)

# Initialisation de l'état de navigation
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'doc_type' not in st.session_state:
    st.session_state.doc_type = None

# --- FONCTION DE GÉNÉRATION PDF ---
def generate_pdf(name, content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt="RAPPORT D'EXPERTISE DOCKIMMO", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=11)
    # Nettoyage pour éviter les erreurs d'encodage PDF
    clean_text = content.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, txt=clean_text)
    return pdf.output(dest='S').encode('latin-1')

# 2. Style CSS Harmonisé
st.markdown("""
    <style>
    /* Fond et polices */
    .stApp { background-color: #f8f9fa; }
    h1, h2, h3 { color: #1e3a8a !important; font-family: 'Helvetica Neue', sans-serif; text-align: center; }
    
    /* Centrage de la page d'accueil */
    .main-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding-top: 50px;
    }

    /* Style des boutons (Cartes cliquables) */
    .stButton>button {
        background: white !important;
        color: #1e3a8a !important;
        border: 2px solid #e5e7eb !important;
        border-radius: 12px !important;
        width: 100% !important;
        height: 4.5em !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
    }
    
    .stButton>button:hover {
        border-color: #007BFF !important;
        background-color: #f0f7ff !important;
        transform: translateY(-3px);
        box-shadow: 0 8px 15px rgba(0,123,255,0.1) !important;
    }

    /* Bouton d'action principal (Analyse) */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #007BFF 0%, #0056b3 100%) !important;
        color: white !important;
        border: none !important;
    }

    /* Conteneur du rapport */
    .report-container {
        background-color: white;
        padding: 30px;
        border-radius: 15px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    
    /* Centrage des sous-titres */
    .subtitle {
        text-align: center;
        color: #6b7280;
        font-size: 1.2rem;
        margin-bottom: 40px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTIONS DE NAVIGATION ---
def select_doc(doc_name):
    st.session_state.doc_type = doc_name
    st.session_state.page = 'analysis'

def go_home():
    st.session_state.page = 'home'
    st.session_state.doc_type = None

# ==========================================
# LOGIQUE DES PAGES
# ==========================================

# --- PAGE D'ACCUEIL ---
if st.session_state.page == 'home':
    # Espace pour descendre le contenu
    st.markdown("<div class='main-container'>", unsafe_allow_html=True)
    
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        st.image("https://cdn-icons-png.flaticon.com/512/602/602175.png", width=100)
        st.markdown("<h1>Bienvenue sur DOCKIMMO</h1>", unsafe_allow_html=True)
        st.markdown("<p class='subtitle'>Quel document souhaitez-vous analyser ?</p>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

    # Grille de sélection centrée
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("### 📋 Copropriété")
        if st.button("PV d'Assemblée Générale"): select_doc("PV d'Assemblée Générale")
        if st.button("Rapport de gestion"): select_doc("Rapport de gestion")
        
    with c2:
        st.markdown("### 🛠️ Technique")
        if st.button("Diagnostics (DPE, etc.)"): select_doc("Diagnostics techniques")
        if st.button("Carnet d'entretien"): select_doc("Carnet d'entretien")
        
    with c3:
        st.markdown("### 📜 Juridique")
        if st.button("Bail de location"): select_doc("Bail")
        if st.button("Mandat immobilier"): select_doc("Mandat")

# --- PAGE D'ANALYSE ---
else:
    # Barre de navigation haute
    col_back, col_title_an = st.columns([1, 8])
    with col_back:
        if st.button("⬅️ Retour"): go_home()
    with col_title_an:
        st.markdown(f"<h2 style='text-align:left; margin-top:0;'>Analyse : {st.session_state.doc_type}</h2>", unsafe_allow_html=True)

    st.divider()

    # Sidebar pour les paramètres
    st_api_key = st.secrets.get("OPENAI_API_KEY", "")
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        api_key = st.text_input("Clé API OpenAI", value=st_api_key, type="password")
        st.info(f"Analyseur actif : {st.session_state.doc_type}")

    # Layout de l'interface d'analyse
    col_input, col_report = st.columns([1, 2], gap="large")

    with col_input:
        st.markdown("### 📤 Document")
        uploaded_file = st.file_uploader(f"Déposez le fichier PDF ici", type="pdf")
        # Bouton avec style primaire (dégradé bleu)
        analyze_btn = st.button("Lancer l'expertise intelligente ✨", type="primary")

    with col_report:
        st.markdown("### 📋 Rapport d'expertise")
        
        if analyze_btn and uploaded_file and api_key:
            with st.spinner("Analyse approfondie en cours..."):
                try:
                    # Extraction texte (10 premières pages pour plus de contexte)
                    reader = PyPDF2.PdfReader(uploaded_file)
                    text = "".join([p.extract_text() or "" for p in reader.pages[:10]])
                    client = OpenAI(api_key=api_key)
                    
                    prompt = f"Expert immobilier. Analyse ce {st.session_state.doc_type}. Extraits METRIC1: [Objet], METRIC2: [Info clé financière], METRIC3: [Risque/Alerte]. Puis un rapport structuré."

                    # Gestion Vision si texte pauvre
                    if len(text.strip()) < 200:
                        images = convert_from_bytes(uploaded_file.getvalue(), last_page=2)
                        content = [{"type": "text", "text": prompt}]
                        for img in images:
                            buf = io.BytesIO()
                            img.save(buf, format="JPEG")
                            img_b64 = base64.b64encode(buf.getvalue()).decode()
                            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}})
                        messages = [{"role": "user", "content": content}]
                    else:
                        messages = [{"role": "user", "content": f"{prompt}\n\nTexte:\n{text}"}]

                    response = client.chat.completions.create(model="gpt-4o", messages=messages, temperature=0)
                    full_res = response.choices[0].message.content

                    # Extraction Metrics
                    lines = full_res.split('\n')
                    m1 = next((l.split(': ')[1] for l in lines if "METRIC1" in l), "Inconnu")
                    m2 = next((l.split(': ')[1] for l in lines if "METRIC2" in l), "N/A")
                    m3 = next((l.split(': ')[1] for l in lines if "METRIC3" in l), "N/A")

                    # Affichage visuel
                    st.markdown("---")
                    mc1, mc2, mc3 = st.columns(3)
                    mc1.metric("📌 Objet", m1)
                    mc2.metric("💰 Détail clé", m2)
                    mc3.metric("⚠️ Risque", m3)
                    st.markdown("---")

                    # Affichage du rapport dans son conteneur blanc
                    report_body = full_res.split('---')[-1]
                    st.markdown(f'<div class="report-container">{report_body}</div>', unsafe_allow_html=True)
                    
                    # Génération et téléchargement PDF
                    pdf_data = generate_pdf(m1, report_body)
                    st.download_button(
                        label="📥 Télécharger l'expertise (PDF)",
                        data=pdf_data,
                        file_name=f"DOCKIMMO_{st.session_state.doc_type.replace(' ', '_')}.pdf",
                        mime="application/pdf"
                    )

                except Exception as e:
                    st.error(f"Une erreur est survenue : {e}")
