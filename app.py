import streamlit as st
from openai import OpenAI
import PyPDF2
import io
import base64
from pdf2image import convert_from_bytes
from PIL import Image
from fpdf import FPDF

# ==========================================
# 1. CONFIGURATION ET ETAT
# ==========================================
st.set_page_config(
    page_title="DOCKIMMO | Expert IA",
    page_icon="🏠",
    layout="wide"
)

if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'doc_type' not in st.session_state:
    st.session_state.doc_type = None

# ==========================================
# 2. STYLE CSS CUMULÉ (Design + Centrage + Alignement)
# ==========================================
st.markdown("""
    <style>
    /* Fond et base */
    .stApp { background-color: #f8f9fa; }
    
    /* Harmonisation des titres */
    h1, h2 { color: #1e3a8a !important; text-align: center !important; }
    
    /* ALIGNEMENT PRÉCIS DES COLONNES */
    [data-testid="column"] {
        display: flex;
        flex-direction: column;
        align-items: center !important; /* Centre tout horizontalement */
        justify-content: flex-start;
    }

    /* Style des titres de colonnes (supprime le décalage) */
    .column-header {
        color: #1e3a8a;
        font-weight: 700;
        font-size: 1.4rem;
        margin-bottom: 25px; /* Espace constant avant les boutons */
        margin-top: 10px;
        text-align: center;
        min-height: 40px;
        display: flex;
        align-items: center;
    }

    /* BOUTONS DOCKIMMO (Style cumulé) */
    .stButton {
        width: 100%;
        display: flex;
        justify-content: center;
    }
    
    .stButton>button {
        width: 90% !important;
        background: white !important;
        color: #1e3a8a !important;
        border: 2px solid #e5e7eb !important;
        border-radius: 12px !important;
        height: 4.2em !important;
        font-weight: 600 !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        margin-bottom: 12px;
    }
    
    .stButton>button:hover {
        border-color: #007BFF !important;
        background-color: #f0f7ff !important;
        transform: translateY(-3px);
        box-shadow: 0 5px 15px rgba(0,123,255,0.1) !important;
    }

    /* BOUTON ANALYSE (Couleur primaire) */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #007BFF 0%, #0056b3 100%) !important;
        color: white !important;
        border: none !important;
    }

    /* Rapport Container */
    .report-container {
        background-color: white;
        padding: 30px;
        border-radius: 15px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. LOGIQUE & FONCTIONS
# ==========================================
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

def select_doc(doc_name):
    st.session_state.doc_type = doc_name
    st.session_state.page = 'analysis'

def go_home():
    st.session_state.page = 'home'
    st.session_state.doc_type = None

# ==========================================
# 4. PAGE D'ACCUEIL
# ==========================================
if st.session_state.page == 'home':
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Logo et Bienvenue centrés
    _, col_center, _ = st.columns([1, 2, 1])
    with col_center:
        st.image("https://cdn-icons-png.flaticon.com/512/602/602175.png", width=100)
        st.markdown("<h1>Bienvenue sur DOCKIMMO</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; font-size:1.2rem; color:#6b7280;'>Quel document souhaitez-vous analyser ?</p>", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # Grille de sélection (3 colonnes)
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("<div class='column-header'>📋 Copropriété</div>", unsafe_allow_html=True)
        if st.button("PV d'Assemblée Générale"): select_doc("PV d'Assemblée Générale")
        if st.button("Rapport de gestion"): select_doc("Rapport de gestion")
        
    with c2:
        st.markdown("<div class='column-header'>🛠️ Technique</div>", unsafe_allow_html=True)
        if st.button("Diagnostics (DPE, etc.)"): select_doc("Diagnostics techniques")
        if st.button("Carnet d'entretien"): select_doc("Carnet d'entretien")
        
    with c3:
        st.markdown("<div class='column-header'>📜 Juridique</div>", unsafe_allow_html=True)
        if st.button("Bail de location"): select_doc("Bail")
        if st.button("Mandat immobilier"): select_doc("Mandat")

# ==========================================
# 5. PAGE D'ANALYSE
# ==========================================
else:
    # Barre de navigation
    col_back, col_title_an = st.columns([1, 8])
    with col_back:
        if st.button("⬅️ Retour"): go_home()
    with col_title_an:
        st.markdown(f"<h2 style='text-align:left !important; margin:0;'>Expertise : {st.session_state.doc_type}</h2>", unsafe_allow_html=True)

    st.divider()

    # Sidebar Secrets / API
    st_api_key = st.secrets.get("OPENAI_API_KEY", "")
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        api_key = st.text_input("Clé API OpenAI", value=st_api_key, type="password")
        st.write(f"Document : **{st.session_state.doc_type}**")

    # Layout Interface
    col_input, col_report = st.columns([1, 2], gap="large")

    with col_input:
        st.markdown("### 📤 Téléchargement")
        uploaded_file = st.file_uploader(f"Chargez le PDF", type="pdf")
        analyze_btn = st.button("Lancer l'audit intelligent ✨", type="primary")

    with col_report:
        st.markdown("### 📋 Rapport d'expertise")
        
        if analyze_btn and uploaded_file and api_key:
            with st.spinner("Analyse en cours..."):
                try:
                    # Extraction
                    reader = PyPDF2.PdfReader(uploaded_file)
                    text = "".join([p.extract_text() or "" for p in reader.pages[:10]])
                    client = OpenAI(api_key=api_key)
                    
                    prompt = f"Expert immo. Analyse {st.session_state.doc_type}. METRIC1: [Sujet], METRIC2: [Détail financier], METRIC3: [Risque]. Rapport structuré ensuite."

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

                    # Metrics
                    lines = full_res.split('\n')
                    m1 = next((l.split(': ')[1] for l in lines if "METRIC1" in l), "N/A")
                    m2 = next((l.split(': ')[1] for l in lines if "METRIC2" in l), "N/A")
                    m3 = next((l.split(': ')[1] for l in lines if "METRIC3" in l), "N/A")

                    st.markdown("---")
                    mc1, mc2, mc3 = st.columns(3)
                    mc1.metric("📌 Objet", m1)
                    mc2.metric("💰 Détail", m2)
                    mc3.metric("⚠️ Risque", m3)
                    st.markdown("---")

                    # Affichage Rapport
                    report_body = full_res.split('---')[-1]
                    st.markdown(f'<div class="report-container">{report_body}</div>', unsafe_allow_html=True)
                    
                    # PDF Download
                    pdf_data = generate_pdf(m1, report_body)
                    st.download_button(
                        label="📥 Télécharger le rapport (PDF)",
                        data=pdf_data,
                        file_name=f"Expertise_{st.session_state.doc_type.replace(' ', '_')}.pdf",
                        mime="application/pdf"
                    )

                except Exception as e:
                    st.error(f"Erreur : {e}")
