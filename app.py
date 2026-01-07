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
    clean_text = content.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, txt=clean_text)
    return pdf.output(dest='S').encode('latin-1')

# 2. Style CSS Fusionné
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    h1, h2, h3 { color: #1e3a8a !important; font-family: 'Helvetica Neue', sans-serif; }
    
    /* Style des boutons de la page d'accueil */
    .stButton>button {
        background: linear-gradient(90deg, #007BFF 0%, #0056b3 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        height: 3.5em !important;
        font-weight: bold !important;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,123,255,0.3);
    }
    
    .report-container {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e5e7eb;
    }
    
    .welcome-card {
        text-align: center;
        padding: 20px;
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
    st.markdown("<div class='welcome-card'>", unsafe_allow_html=True)
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        st.image("https://cdn-icons-png.flaticon.com/512/602/602175.png", width=100)
        st.markdown("<h1>Bienvenue sur DOCKIMMO</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; font-size:1.2rem; color:#6b7280;'>Quel document souhaitez-vous analyser ?</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    # Grille de choix
    c1, c2, c3 = st.columns(3)
    with c1:
        st.subheader("📋 Copropriété")
        if st.button("PV d'Assemblée Générale"): select_doc("PV d'Assemblée Générale")
        if st.button("Rapport de gestion"): select_doc("Rapport de gestion")
    with c2:
        st.subheader("🏗️ Technique")
        if st.button("Diagnostics (DPE, etc.)"): select_doc("Diagnostics techniques")
        if st.button("Carnet d'entretien"): select_doc("Carnet d'entretien")
    with c3:
        st.subheader("⚖️ Juridique")
        if st.button("Bail de location"): select_doc("Bail")
        if st.button("Mandat immobilier"): select_doc("Mandat")

# --- PAGE D'ANALYSE ---
else:
    # Header de la page d'analyse
    col_back, col_title = st.columns([1, 5])
    with col_back:
        if st.button("⬅️ Retour"): go_home()
    with col_title:
        st.markdown(f"<h2>Analyse de : {st.session_state.doc_type}</h2>", unsafe_allow_html=True)

    st.divider()

    # Sidebar pour la clé API (toujours accessible en analyse)
    st_api_key = st.secrets.get("OPENAI_API_KEY", "")
    with st.sidebar:
        st.markdown("### ⚙️ Paramètres")
        api_key = st.text_input("Clé API OpenAI", value=st_api_key, type="password")
        st.info(f"Analyse en cours : {st.session_state.doc_type}")

    # Corps de l'analyse
    col_input, col_report = st.columns([1, 2], gap="large")

    with col_input:
        st.subheader("📤 Chargement")
        uploaded_file = st.file_uploader(f"Déposez votre {st.session_state.doc_type} (PDF)", type="pdf")
        analyze_btn = st.button("Lancer l'audit ✨")

    with col_report:
        st.subheader("📋 Rapport d'expertise")
        
        if analyze_btn and uploaded_file and api_key:
            with st.spinner("L'IA examine le document..."):
                try:
                    # Extraction texte
                    reader = PyPDF2.PdfReader(uploaded_file)
                    text = "".join([p.extract_text() or "" for p in reader.pages[:5]])
                    client = OpenAI(api_key=api_key)
                    
                    # Prompt adapté au type de document choisi
                    prompt = f"Tu es un expert immobilier. Analyse ce document : {st.session_state.doc_type}. Donne METRIC1: [Sujet principal], METRIC2: [Info clé/Montant], METRIC3: [Alerte/Risque]. Puis un rapport complet."

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

                    # Affichage des Metrics
                    st.markdown("---")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("📌 Sujet", m1)
                    c2.metric("💰 Info Clé", m2)
                    c3.metric("⚠️ Risque", m3)
                    st.markdown("---")

                    # Rapport
                    report_body = full_res.split('---')[-1]
                    st.markdown(f'<div class="report-container">{report_body}</div>', unsafe_allow_html=True)
                    
                    # Bouton PDF
                    pdf_data = generate_pdf(m1, report_body)
                    st.download_button(
                        label="📥 Télécharger le rapport (PDF)",
                        data=pdf_data,
                        file_name=f"Expertise_DOCKIMMO_{st.session_state.doc_type}.pdf",
                        mime="application/pdf"
                    )

                except Exception as e:
                    st.error(f"Erreur technique : {e}")
