import streamlit as st
from openai import OpenAI
import PyPDF2
import io
import base64
from pdf2image import convert_from_bytes
from PIL import Image
from fpdf import FPDF

# 1. Configuration de la page (DOIT être la première commande Streamlit)
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
    pdf.cell(200, 10, txt="RAPPORT D'EXPERTISE DOCKIMMO", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=11)
    clean_text = content.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, txt=clean_text)
    return pdf.output(dest='S').encode('latin-1')

# 2. Style CSS (C'est ce bloc qui change l'apparence)
st.markdown("""
    <style>
    /* Change le fond en gris clair */
    .stApp { background-color: #f8f9fa; }
    
    /* Style des titres en bleu DockImmo */
    h1, h2, h3 { color: #1e3a8a !important; font-family: 'Helvetica Neue', sans-serif; }
    
    /* Bouton d'analyse en dégradé bleu */
    .stButton>button {
        background: linear-gradient(90deg, #007BFF 0%, #0056b3 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        height: 3.5em !important;
        font-weight: bold !important;
    }
    
    /* Style des encadrés de texte (Rapport) */
    .report-container {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e5e7eb;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Header Épuré (Logo + Titre)
col_logo, col_title = st.columns([1, 5])
with col_logo:
    # Icône seule (sans texte anglais)
    st.image("https://cdn-icons-png.flaticon.com/512/602/602175.png", width=80)
with col_title:
    st.markdown("<h1 style='margin-bottom:0;'>DOCKIMMO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:1.2rem; color:#6b7280; margin-top:0;'>Expertise augmentée par Intelligence Artificielle</p>", unsafe_allow_html=True)

st.divider()

# 4. Sidebar pour la clé API
st_api_key = st.secrets.get("OPENAI_API_KEY", "")
with st.sidebar:
    st.markdown("### ⚙️ Paramètres")
    api_key = st.text_input("Clé API OpenAI", value=st_api_key, type="password")
    st.info("Le mode Vision est actif pour les scans.")

# 5. Interface Principale
col_input, col_report = st.columns([1, 2], gap="large")

with col_input:
    st.subheader("📤 Document")
    doc_type = st.selectbox("Type de document", ["PV d'Assemblée Générale", "DPE", "Rapport de gestion"])
    uploaded_file = st.file_uploader("Déposez votre PDF", type="pdf")
    analyze_btn = st.button("Lancer l'audit ✨")

with col_report:
    st.subheader("📋 Rapport d'expertise")
    
    if analyze_btn and uploaded_file and api_key:
        with st.spinner("Analyse en cours..."):
            try:
                # --- EXTRACTION ---
                reader = PyPDF2.PdfReader(uploaded_file)
                text = "".join([p.extract_text() or "" for p in reader.pages[:5]])
                client = OpenAI(api_key=api_key)
                
                prompt = f"Expert immo. Analyse {doc_type}. Donne METRIC1: [Nom], METRIC2: [Total Travaux €], METRIC3: [Risque]. Puis un rapport détaillé."

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

                # --- AFFICHAGE ---
                lines = full_res.split('\n')
                m1 = next((l.split(': ')[1] for l in lines if "METRIC1" in l), "Inconnu")
                m2 = next((l.split(': ')[1] for l in lines if "METRIC2" in l), "0 €")
                m3 = next((l.split(': ')[1] for l in lines if "METRIC3" in l), "N/A")

                # Metrics
                st.markdown("---")
                c1, c2, c3 = st.columns(3)
                c1.metric("👤 Propriétaire", m1)
                c2.metric("🏗️ Travaux", m2)
                c3.metric("⚠️ Risque", m3)
                st.markdown("---")

                # Rapport
                report_body = full_res.split('---')[-1]
                st.markdown(f'<div class="report-container">{report_body}</div>', unsafe_allow_html=True)
                
                # Bouton PDF
                pdf_data = generate_pdf(m1, report_body)
                st.download_button(
                    label="📥 Télécharger le PDF",
                    data=pdf_data,
                    file_name=f"Expertise_{m1}.pdf",
                    mime="application/pdf"
                )

            except Exception as e:
                st.error(f"Erreur : {e}")
