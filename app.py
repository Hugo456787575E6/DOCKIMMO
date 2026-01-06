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
                    # --- EXTRACTION DU TEXTE ---
                    reader = PyPDF2.PdfReader(uploaded_file)
                    pages_text = []
                    for page in reader.pages[:20]: # Analyse jusqu'à 20 pages
                        t = page.extract_text()
                        if t:
                            pages_text.append(t)
                    
                    text = "\n".join(pages_text)

                    # Vérification si le PDF contient du texte
                    if len(text.strip()) < 50:
                        st.error("❌ Le texte du PDF n'a pas pu être extrait. Est-ce un scan (image) ?")
                        st.stop()
                    
                    # --- APPEL OPENAI ---
                    client = OpenAI(api_key=api_key)
                    
                    prompt = f"""Tu es un expert en audit immobilier professionnel. 
                    ANALYSE LE TEXTE CI-DESSOUS ({doc_type}) ET EXTRAIS LES INFOS.
                    
                    D'abord, donne obligatoirement ces 3 lignes :
                    METRIC1: [Résumé état général]
                    METRIC2: [Total travaux votés en €]
                    METRIC3: [Risque: Faible, Modéré ou Critique]

                    Rapport détaillé ensuite (utilise des titres et des listes à puces) :
                    ### 🏗️ Travaux et Entretien
                    ### 💰 Situation Financière
                    ### ⚠️ Points de Vigilance
                    ### 📝 Synthèse de l'Expert

                    TEXTE DU DOCUMENT :
                    {text}"""

                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "Tu es un expert immobilier. Tu analyses le texte fourni et ne l'inventes pas."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.2
                    )
                    
                    full_res = response.choices[0].message.content

                    # --- NETTOYAGE ET AFFICHAGE ---
                    lines = full_res.split('\n')
                    m1_v = next((l.split(': ')[1] for l in lines if "METRIC1" in l), "N/A")
                    m2_v = next((l.split(': ')[1] for l in lines if "METRIC2" in l), "0 €")
                    m3_v = next((l.split(': ')[1] for l in lines if "METRIC3" in l), "Inconnu")
                    
                    clean_report = "\n".join([l for l in lines if "METRIC" not in l])

                    # Affichage des Metrics
                    c_a, c_b, c_c = st.columns(3)
                    with c_a:
                        st.info("**État**")
                        st.subheader(m1_v)
                    with c_b:
                        st.success("**Travaux**")
                        st.subheader(m2_v)
                    with c_c:
                        st.warning("**Risque**")
                        st.subheader(m3_v)
                    
                    st.divider()
                    st.markdown(clean_report)
                    st.success("✅ Analyse terminée avec succès !")

                except Exception as e:
                    st.error(f"Erreur technique : {e}")
