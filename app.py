import streamlit as st
from openai import OpenAI
import PyPDF2

# 1. Configuration de la page
st.set_page_config(
    page_title="DOCKIMMO - Expert IA",
    page_icon="🏠",
    layout="wide"
)

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

# 3. Gestion de la clé API (Automatique via Secrets)
st_api_key = st.secrets.get("OPENAI_API_KEY", "")

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/602/602175.png", width=100)
    st.title("Configuration")
    api_key = st.text_input("Clé API OpenAI", value=st_api_key, type="password")
    st.divider()
    st.info("Analyse intelligente de PV d'AG et diagnostics.")

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
            with st.spinner("L'IA examine le document..."):
                try:
                    try:
                    reader = PyPDF2.PdfReader(uploaded_file)
                    pages_text = []
                    for page in reader.pages[:20]: # On monte à 20 pages au cas où
                        t = page.extract_text()
                        if t:
                            pages_text.append(t)
                    
                    text = "\n".join(pages_text)

                    if len(text.strip()) < 50:
                        st.error("❌ Le texte du PDF n'a pas pu être extrait. Est-ce un scan ?")
                        st.info("Conseil : Essayez avec un PDF contenant du texte sélectionnable.")
                        st.stop()
                    
                    client = OpenAI(api_key=api_key)
                    
                    # On demande explicitement à l'IA d'analyser le texte fourni dessous
                    prompt = f"""Tu es un expert en audit immobilier. 
                    ANALYSE LE TEXTE DU DOCUMENT CI-DESSOUS ET EXTRAIS LES INFOS.
                    
                    D'abord, donne obligatoirement ces 3 lignes :
                    METRIC1: [Résumé état]
                    METRIC2: [Total travaux en €]
                    METRIC3: [Risque: Faible, Modéré ou Critique]

                    Rapport détaillé ensuite :
                    ### 🏗️ Travaux
                    ### 💰 Finances
                    ### ⚠️ Risques
                    ### 📝 Synthèse

                    TEXTE DU DOCUMENT À ANALYSER :
                    {text}"""

                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "Tu es un assistant qui analyse des documents immobiliers. Tu ne réponds qu'en te basant sur le texte fourni."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.2 # On baisse la température pour plus de précision
                    )
