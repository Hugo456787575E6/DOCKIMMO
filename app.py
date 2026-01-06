import streamlit as st
from openai import OpenAI
import PyPDF2

# Configuration de la page
st.set_page_config(
    page_title="DOCKIMMO - Assistant Expert",
    page_icon="🏠",
    layout="wide"
)

# --- STYLE CSS PERSONNALISÉ ---
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
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        white-space: pre-wrap;
    }
    </style>
    """, unsafe_allow_html=True)

# --- GESTION DE LA CLÉ API ---
# On récupère la clé dans les secrets de Streamlit. 
# Si elle n'existe pas, on met une chaîne vide.
st_api_key = st.secrets.get("OPENAI_API_KEY", "")

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/602/602175.png", width=100)
    st.title("Configuration")
    
    # On utilise la clé des secrets comme valeur par défaut
    api_key = st.text_input(
        "Clé API OpenAI", 
        value=st_api_key, 
        type="password", 
        help="La clé est chargée automatiquement depuis les Secrets."
    )
    
    st.divider()
    st.info("L'analyse démarre dès que vous séléctionnez un PDF et cliquez sur le bouton.")

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
    
    if analyze_btn:
        # Diagnostic immédiat pour comprendre pourquoi ça ne se lance pas
        if not uploaded_file:
            st.error("❌ Veuillez charger un fichier PDF dans la colonne de gauche.")
        elif not api_key:
            # On essaye de récupérer la clé des secrets si le champ texte est vide
            api_key = st.secrets.get("OPENAI_API_KEY", "")
            if not api_key:
                st.error("❌ Clé API introuvable. Tapez-la dans la barre latérale.")
        
        # Si tout est OK, on lance l'analyse
        if uploaded_file and api_key:
            with st.spinner("Analyse approfondie en cours..."):
                try:
                    # Initialisation du client avec la clé trouvée
                    client = OpenAI(api_key=api_key)
                    
                    reader = PyPDF2.PdfReader(uploaded_file)
                    text = "".join([page.extract_text() for page in reader.pages[:15]])
                    
                    # Ton prompt et la suite du code...
                    st.success("✅ Connexion réussie à l'IA !")
                    
                    # [METTRE ICI TON CODE DE REQUÊTE OPENAI ET D'AFFICHAGE]
                    
                except Exception as e:
                    st.error(f"Erreur technique : {e}")
 
