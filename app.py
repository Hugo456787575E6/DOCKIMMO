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
                    # Lecture du PDF
                    reader = PyPDF2.PdfReader(uploaded_file)
                    text = "".join([page.extract_text() for page in reader.pages[:15]])
                    
                    # Appel OpenAI
                    client = OpenAI(api_key=api_key)
                    
                    prompt = f"""Tu es un expert en immobilier. Analyse ce {doc_type}.
                    Extraits d'abord ces 3 données :
                    METRIC1: [Résumé de l'état général en 3 mots]
                    METRIC2: [Total des travaux votés en €]
                    METRIC3: [Risque: Faible, Modéré ou Critique]

                    Fais ensuite un rapport structuré avec des titres et des puces :
                    ### 🏗️ Travaux & Entretien
                    (Détaille les travaux votés, montants et calendrier)
                    
                    ### 💰 Situation Financière
                    (Budget, impayés, fonds travaux)
                    
                    ### ⚠️ Points de Vigilance
                    (Litiges, procédures, urgences)
                    
                    ### 📝 Conclusion de l'expert
                    (Ton avis sur l'opportunité d'achat)
                    
                    Document : {text}"""

                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": prompt}]
                    )
                    
                    full_res = response.choices[0].message.content
                    
                    # Découpage pour l'affichage
                    lines = full_res.split('\n')
                    m1_v = next((l.split(': ')[1] for l in lines if "METRIC1" in l), "N/A")
                    m2_v = next((l.split(': ')[1] for l in lines if "METRIC2" in l), "0 €")
                    m3_v = next((l.split(': ')[1] for l in lines if "METRIC3" in l), "Inconnu")
                    
                    clean_report = "\n".join([l for l in lines if "METRIC" not in l])

                    # Affichage des résultats
                    c_a, c_b, c_c = st.columns(3)
                    c_a.metric("État", m1_v)
                    c_b.metric("Travaux", m2_v)
                    c_c.metric("Risque", m3_v)
                    
                    st.divider()
                    st.markdown(f'<div class="report-box">{clean_report}</div>', unsafe_allow_html=True)
                    st.success("Analyse terminée avec succès !")

                except Exception as e:
                    st.error(f"Erreur lors de l'analyse : {e}")
