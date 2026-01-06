import streamlit as st
from openai import OpenAI
import PyPDF2

# Configuration de la page (Favicon et titre de l'onglet)
st.set_page_config(
    page_title="ImmoAI - Assistant Expert",
    page_icon="🏠",
    layout="wide"
)

# --- STYLE CSS PERSONNALISÉ ---
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #007BFF;
        color: white;
    }
    .report-box {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/602/602175.png", width=100) # Logo temporaire
    st.title("Configuration")
    api_key = st.text_input("Clé API OpenAI", type="password", help="Votre clé reste confidentielle.")
    st.divider()
    st.info("Cet outil analyse vos PV d'AG et diagnostics techniques en quelques secondes.")

# --- CORPS PRINCIPAL ---
col1, col2 = st.columns([1, 2], gap="large")

with col1:
    st.subheader("📤 Document à analyser")
    doc_type = st.selectbox(
        "Quel type de document ?",
        ["PV d'Assemblée Générale", "Dossier de Diagnostics (DPE)", "Rapport de gestion"]
    )
    
    uploaded_file = st.file_uploader("Glissez le PDF ici", type="pdf")
    
    analyze_btn = st.button("Lancer l'analyse magique ✨")

with col2:
    st.subheader("📋 Résultat de l'analyse")
    
    if analyze_btn and uploaded_file and api_key:
        with st.spinner("Analyse approfondie en cours..."):
            try:
                reader = PyPDF2.PdfReader(uploaded_file)
                # On prend un peu plus de texte pour être précis (15 pages)
                text = "".join([page.extract_text() for page in reader.pages[:15]])
                
                client = OpenAI(api_key=api_key)
                
                # Prompt Ingénierie : On demande un format strict pour le code
                prompt = f"""Tu es un expert en audit immobilier. Analyse ce {doc_type}.
                D'abord, donne ces 3 infos sous ce format :
                METRIC1: [Un résumé de 2 mots sur l'énergie ou l'état général]
                METRIC2: [Le montant total des travaux trouvés ou '0 €']
                METRIC3: [Le niveau de risque : Faible, Modéré ou Critique]
                
                Ensuite, fais ton rapport détaillé :
                1. TRAVAUX : Liste les travaux votés, montants et dates.
                2. FINANCES : Budget prévisionnel et fonds de travaux.
                3. RISQUES : Litiges, impayés ou alertes.
                4. SYNTHÈSE : Ton avis pro.
                
                Document : {text}"""

                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}]
                )
                full_text = response.choices[0].message.content

                # --- EXTRACTION LOGIQUE DES METRICS ---
                # On sépare les lignes pour isoler METRIC1, 2 et 3
                lines = full_text.split('\n')
                m1_val = next((l.split(': ')[1] for l in lines if "METRIC1" in l), "N/A")
                m2_val = next((l.split(': ')[1] for l in lines if "METRIC2" in l), "0 €")
                m3_val = next((l.split(': ')[1] for l in lines if "METRIC3" in l), "Inconnu")
                
                # Nettoyage du rapport pour enlever les lignes techniques METRIC
                clean_report = "\n".join([l for l in lines if "METRIC" not in l])

                # --- AFFICHAGE ---
                m1, m2, m3 = st.columns(3)
                m1.metric("État / Énergie", m1_val)
                m2.metric("Budget Travaux", m2_val)
                m3.metric("Niveau de Risque", m3_val)

                st.divider()
                st.markdown(f'<div class="report-box">{clean_report}</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Erreur technique : {e}")
 