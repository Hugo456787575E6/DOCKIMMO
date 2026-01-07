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
    page_title="DOCKIMMO - Expert IA",
    page_icon="🏠",
    layout="wide"
)

# --- FONCTION DE GÉNÉRATION PDF ---
def generate_pdf(name, content):
    pdf = FPDF()
    pdf.add_page()
    
    # Titre
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt="RAPPORT D'EXPERTISE IMMOBILIERE", ln=True, align='C')
    pdf.ln(10)
    
    # Corps du texte
    pdf.set_font("Arial", size=11)
    # Nettoyage des caractères spéciaux pour éviter les erreurs d'encodage
    clean_text = content.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, txt=clean_text)
    
    return pdf.output(dest='S').encode('latin-1')

# 2. Style CSS
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #007BFF;
        color: white;
    }
    .report-box {
        background-color: white;
        padding: 25px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        line-height: 1.6;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Gestion de la clé API
st_api_key = st.secrets.get("OPENAI_API_KEY", "")

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/602/602175.png", width=100)
    st.title("Configuration")
    api_key = st.text_input("Clé API OpenAI", value=st_api_key, type="password")
    st.divider()
    st.info("Mode Vision actif : l'IA analysera les images si le texte est absent.")

# 4. Corps principal
col1, col2 = st.columns([1, 2], gap="large")

with col1:
    st.subheader("📤 Document")
    doc_type = st.selectbox("Type de document", ["PV d'Assemblée Générale", "DPE", "Rapport de gestion"])
    uploaded_file = st.file_uploader("Charger le PDF", type="pdf")
    analyze_btn = st.button("Lancer l'analyse magique ✨")

with col2:
    st.subheader("📋 Rapport d'expertise")
    
    if analyze_btn:
        if not uploaded_file:
            st.error("Veuillez charger un fichier PDF.")
        elif not api_key:
            st.error("Clé API manquante.")
        else:
            with st.spinner("L'IA examine le document... (Le mode Vision peut prendre 30s)"):
                try:
                    # --- EXTRACTION DU TEXTE ---
                    reader = PyPDF2.PdfReader(uploaded_file)
                    extracted_text = ""
                    for page in reader.pages[:10]:
                        extracted_text += page.extract_text() or ""

                    client = OpenAI(api_key=api_key)
                    
                    # --- DÉFINITION DU PROMPT CHIRURGICAL ---
                    instructions_chirurgicales = f"""Tu es un auditeur expert en copropriété française. 
                    ANALYSE CE DOCUMENT ({doc_type}) AVEC UNE PRÉCISION ABSOLUE.

                    1. IDENTIFICATION : Qui est le destinataire du document ? (Cherche le nom en haut ou dans la feuille de présence).
                    2. TRAVAUX VOTÉS : Liste chaque résolution de travaux approuvée avec son montant total.
                    3. CALCUL INDIVIDUEL : Si tu trouves les millièmes ou la quote-part du copropriétaire (ex: 125/1000è), calcule sa part estimée pour chaque montant de travaux trouvé.
                    4. FINANCES : Note le solde créditeur ou débiteur si mentionné.

                    D'abord, donne impérativement ces 3 lignes :
                    METRIC1: [Nom du copropriétaire identifié]
                    METRIC2: [Total Travaux Copro en €]
                    METRIC3: [Risque: Faible, Modéré ou Critique]

                    Rapport détaillé ensuite :
                    ### 👤 Profil du Copropriétaire
                    ### 🏗️ Travaux et Budget (Détails)
                    ### 💰 État des Charges et Fonds
                    ### ⚠️ Points de Vigilance Spécifiques
                    """

                    # --- LOGIQUE HYBRIDE (TEXTE OU VISION) ---
                    if len(extracted_text.strip()) < 200:
                        st.warning("🔍 Scan détecté. Analyse par images (Vision)...")
                        images = convert_from_bytes(uploaded_file.getvalue(), last_page=3)
                        user_content = [{"type": "text", "text": instructions_chirurgicales}]
                        for img in images:
                            buffered = io.BytesIO()
                            img.save(buffered, format="JPEG")
                            img_b64 = base64.b64encode(buffered.getvalue()).decode()
                            user_content.append({
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
                            })
                        messages = [{"role": "system", "content": "Expert immo."}, {"role": "user", "content": user_content}]
                    else:
                        st.success("📄 Texte détecté. Analyse textuelle rapide...")
                        messages = [
                            {"role": "system", "content": "Expert immo."},
                            {"role": "user", "content": f"{instructions_chirurgicales}\n\nTEXTE :\n{extracted_text}"}
                        ]

                    # --- APPEL À GPT-4o ---
                    response = client.chat.completions.create(model="gpt-4o", messages=messages, temperature=0)
                    full_res = response.choices[0].message.content

                    # --- NETTOYAGE ET AFFICHAGE ---
                    lines = full_res.split('\n')
                    m1_v = next((l.split(': ')[1] for l in lines if "METRIC1" in l), "Non identifié")
                    m2_v = next((l.split(': ')[1] for l in lines if "METRIC2" in l), "0 €")
                    m3_v = next((l.split(': ')[1] for l in lines if "METRIC3" in l), "Inconnu")
                    
                    clean_report = "\n".join([l for l in lines if "METRIC" not in l])

                    # Affichage des Metrics
                    c_a, c_b, c_c = st.columns(3)
                    with c_a:
                        st.info("**Copropriétaire**")
                        st.subheader(m1_v)
                    with c_b:
                        st.success("**Total Travaux**")
                        st.subheader(m2_v)
                    with c_c:
                        st.warning("**Niveau de Risque**")
                        st.subheader(m3_v)
                    
                    st.divider()
                    st.markdown(clean_report)
                    
                    # --- BOUTON PDF ---
                    pdf_bytes = generate_pdf(m1_v, clean_report)
                    st.download_button(
                        label="📥 Télécharger le rapport en PDF",
                        data=pdf_bytes,
                        file_name=f"Rapport_DOCKIMMO_{m1_v.replace(' ', '_')}.pdf",
                        mime="application/pdf"
                    )
                    
                    st.success("✅ Analyse personnalisée terminée !")

                except Exception as e:
                    st.error(f"Erreur technique : {e}")
