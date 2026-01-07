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

# --- FONCTION DE GÉNÉRATION PDF ---
def generate_pdf(name, content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt="RAPPORT D'EXPERTISE IMMOBILIERE - DOCKIMMO", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=11)
    # Nettoyage pour compatibilité PDF
    clean_text = content.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, txt=clean_text)
    return pdf.output(dest='S').encode('latin-1')

# 2. Style CSS (Design Premium & Épuré)
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    
    /* Style des titres */
    h1, h2, h3 { color: #1e3a8a; font-family: 'Helvetica Neue', sans-serif; }
    
    /* Cards Blanches */
    [data-testid="stVerticalBlock"] > div:has(div.stButton) {
        background-color: white;
        padding: 2rem;
        border-radius: 15px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* Style du bouton principal */
    .stButton>button {
        background: linear-gradient(90deg, #007BFF 0%, #0056b3 100%);
        color: white;
        border: none;
        font-weight: bold;
        height: 3.5em;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,123,255,0.3);
    }
    
    /* Metrics Box */
    [data-testid="stMetricValue"] { font-size: 1.8rem; color: #1e3a8a; }
    </style>
    """, unsafe_allow_html=True)

# 3. Header Épuré (Logo + Titre)
col_logo, col_title = st.columns([1, 5])
with col_logo:
    # On affiche uniquement l'icône du logo
    st.image("https://cdn-icons-png.flaticon.com/512/602/602175.png", width=80)
with col_title:
    st.markdown("<h1 style='margin-bottom:0;'>DOCKIMMO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:1.2rem; color:#6b7280; margin-top:0;'>Expertise augmentée par Intelligence Artificielle</p>", unsafe_allow_html=True)

st.divider()

# 4. Sidebar et Paramètres
st_api_key = st.secrets.get("OPENAI_API_KEY", "")
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    api_key = st.text_input("Clé API OpenAI", value=st_api_key, type="password")
    st.divider()
    st.info("L'IA utilise GPT-4o pour analyser les textes et les images scannées.")

# 5. Corps principal
col_input, col_report = st.columns([1, 2], gap="large")

with col_input:
    st.subheader("📤 Document à analyser")
    doc_type = st.selectbox("Type de document", ["PV d'Assemblée Générale", "DPE", "Rapport de gestion"])
    uploaded_file = st.file_uploader("Glissez votre PDF ici", type="pdf")
    analyze_btn = st.button("Lancer l'audit intelligent ✨")

with col_report:
    st.subheader("📋 Rapport d'expertise")
    
    if analyze_btn:
        if not uploaded_file:
            st.error("Veuillez charger un fichier PDF.")
        elif not api_key:
            st.error("Clé API manquante.")
        else:
            with st.spinner("Analyse chirurgicale en cours... (Mode Vision actif)"):
                try:
                    # --- EXTRACTION TEXTE ---
                    reader = PyPDF2.PdfReader(uploaded_file)
                    extracted_text = "".join([p.extract_text() or "" for p in reader.pages[:10]])

                    client = OpenAI(api_key=api_key)
                    
                    instructions = f"""Tu es un auditeur expert en copropriété française. 
                    ANALYSE CE DOCUMENT ({doc_type}) AVEC UNE PRÉCISION ABSOLUE.

                    1. IDENTIFICATION : Nom du destinataire/copropriétaire.
                    2. TRAVAUX VOTÉS : Liste des résolutions approuvées et montants.
                    3. CALCUL INDIVIDUEL : Part du copropriétaire selon ses millièmes.
                    4. FINANCES : État du fonds Alur et dettes éventuelles.

                    D'abord, donne impérativement ces 3 lignes :
                    METRIC1: [Nom du copropriétaire]
                    METRIC2: [Total Travaux Copro €]
                    METRIC3: [Risque: Faible, Modéré ou Critique]

                    Rapport détaillé ensuite avec titres clairs."""

                    # --- LOGIQUE VISION OU TEXTE ---
                    if len(extracted_text.strip()) < 200:
                        st.warning("🔍 Scan détecté. Analyse par images (Vision)...")
                        images = convert_from_bytes(uploaded_file.getvalue(), last_page=3)
                        user_content = [{"type": "text", "text": instructions}]
                        for img in images:
                            buffered = io.BytesIO()
                            img.save(buffered, format="JPEG")
                            img_b64 = base64.b64encode(buffered.getvalue()).decode()
                            user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}})
                        messages = [{"role": "user", "content": user_content}]
                    else:
                        st.success("📄 Texte détecté. Analyse textuelle rapide...")
                        messages = [{"role": "user", "content": f"{instructions}\n\nTEXTE:\n{extracted_text}"}]

                    # --- APPEL IA ---
                    response = client.chat.completions.create(model="gpt-4o", messages=messages, temperature=0)
                    full_res = response.choices[0].message.content

                    # --- EXTRACTION DES DONNÉES CLÉS ---
                    lines = full_res.split('\n')
                    m1_v = next((l.split(': ')[1] for l in lines if "METRIC1" in l), "Non identifié")
                    m2_v = next((l.split(': ')[1] for l in lines if "METRIC2" in l), "0 €")
                    m3_v = next((l.split(': ')[1] for l in lines if "METRIC3" in l), "Inconnu")
                    
                    clean_report = "\n".join([l for l in lines if "METRIC" not in l])

                    # Affichage des Metrics Stylisées
                    st.markdown("---")
                    m_col1, m_col2, m_col3 = st.columns(3)
                    m_col1.metric("👤 Propriétaire", m1_v)
                    m_col2.metric("🏗️ Budget Travaux", m2_v)
                    m_col3.metric("⚠️ Niveau Risque", m3_v)
                    st.markdown("---")

                    # Affichage du Rapport
                    st.markdown(clean_report)
                    
                    # --- BOUTON DE TÉLÉCHARGEMENT PDF ---
                    pdf_bytes = generate_pdf(m1_v, clean_report)
                    st.download_button(
                        label="📥 Télécharger le rapport expert (PDF)",
                        data=pdf_bytes,
                        file_name=f"Expertise_DOCKIMMO_{m1_v.replace(' ', '_')}.pdf",
                        mime="application/pdf"
                    )
                    
                    st.success("✅ Analyse terminée avec succès !")

                except Exception as e:
                    st.error(f"Erreur technique : {e}")
