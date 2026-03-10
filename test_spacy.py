import streamlit as st
import spacy
import os
import PyPDF2
import pdfplumber
import requests
import json

st.set_page_config(page_title="Assistant IA - Documents", layout="wide")

DOSSIER_DOCS = "documents"
if not os.path.exists(DOSSIER_DOCS):
    os.makedirs(DOSSIER_DOCS)

@st.cache_resource
def charger_modele():
    return spacy.load("fr_core_news_md")

nlp = charger_modele()

def lire_fichier(chemin_fichier):
    """Lit un fichier PDF ou TXT et retourne son contenu texte"""
    extension = os.path.splitext(chemin_fichier)[1].lower()
    
    try:
        if extension == '.pdf':
            try:
                texte = ""
                with pdfplumber.open(chemin_fichier) as pdf:
                    for page in pdf.pages:
                        texte += page.extract_text() or ""
                return texte
            except:
                texte = ""
                with open(chemin_fichier, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    for page in pdf_reader.pages:
                        texte += page.extract_text() or ""
                return texte
        
        elif extension == '.txt':
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            for encoding in encodings:
                try:
                    with open(chemin_fichier, 'r', encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            raise ValueError(f"Impossible de décoder {os.path.basename(chemin_fichier)}")
        else:
            return f"Type de fichier non supporté: {extension}"
    
    except Exception as e:
        return f"Erreur lors de la lecture: {str(e)}"

if "messages" not in st.session_state:
    st.session_state.messages = []
if "docs" not in st.session_state:
    st.session_state.docs = {}

st.title("🤖 Assistant IA pour vos Documents")

with st.sidebar:
    st.header("📁 Vos Documents")
    
    # Vérifier si Ollama est disponible
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            st.success("✓ Ollama connecté (GRATUIT)")
            ollama_disponible = True
        else:
            st.warning("⚠️ Ollama non disponible")
            ollama_disponible = False
    except:
        st.error("❌ Ollama non installé")
        st.info("Installez Ollama depuis: https://ollama.com")
        ollama_disponible = False
    
    st.markdown("---")
    
    fichiers_upload = st.file_uploader(
        "Uploader des documents (.txt ou .pdf)", 
        type=['txt', 'pdf'], 
        accept_multiple_files=True
    )
    
    if fichiers_upload:
        for fichier in fichiers_upload:
            chemin = os.path.join(DOSSIER_DOCS, fichier.name)
            with open(chemin, 'wb') as f:
                f.write(fichier.getbuffer())
        st.success(f"✓ {len(fichiers_upload)} fichier(s) sauvegardé(s)")
    
    st.markdown("---")
    
    if st.button("🔄 Charger les documents"):
        with st.spinner("Chargement et extraction..."):
            fichiers = [f for f in os.listdir(DOSSIER_DOCS) 
                       if f.endswith(('.txt', '.pdf'))]
            st.session_state.docs = {}
            
            for fichier in fichiers:
                chemin = os.path.join(DOSSIER_DOCS, fichier)
                contenu = lire_fichier(chemin)
                
                if contenu and not contenu.startswith("Erreur"):
                    st.session_state.docs[fichier] = contenu
                    st.success(f"✓ {fichier}")
                else:
                    st.error(f"✗ {fichier}: {contenu}")
            
            if st.session_state.docs:
                st.success(f"✓ {len(st.session_state.docs)} document(s) chargé(s)")
    
    st.subheader(f"📄 Chargés: {len(st.session_state.docs)}")
    for nom, contenu in st.session_state.docs.items():
        nb_chars = len(contenu)
        icone = "📕" if nom.endswith('.pdf') else "📄"
        st.text(f"{icone} {nom}")
        st.caption(f"   {nb_chars:,} caractères")
    
    if st.button("🗑️ Effacer conversation"):
        st.session_state.messages = []
        st.rerun()

def repondre_avec_ollama(question, documents):
    """Répond en utilisant Ollama (gratuit, local)"""
    
    if not documents:
        return "⚠️ Aucun document chargé. Veuillez d'abord uploader et charger vos documents."
    
    # Créer le contexte
    contexte = ""
    for nom, contenu in documents.items():
        contenu_limite = contenu[:50000]  # Limiter pour Ollama
        contexte += f"\n\n=== Document: {nom} ===\n{contenu_limite}\n"
    
    # Construire le prompt
    prompt = f"""Tu es un assistant expert qui aide à comprendre des documents.

DOCUMENTS:
{contexte}

QUESTION: {question}

INSTRUCTIONS:
- Réponds de manière naturelle et conversationnelle
- Synthétise l'information au lieu de citer des extraits
- Explique avec tes propres mots basés sur le contenu des documents
- Si l'information n'est pas dans les documents, dis-le poliment
- Utilise un ton professionnel mais accessible
- Réponds en français

RÉPONSE:"""
    
    try:
        # Appeler Ollama
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "mistral",
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "Erreur: pas de réponse")
        else:
            return f"❌ Erreur Ollama: {response.status_code}"
    
    except requests.exceptions.ConnectionError:
        return "❌ Impossible de se connecter à Ollama. Assurez-vous qu'Ollama est lancé."
    except Exception as e:
        return f"❌ Erreur: {str(e)}"

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if question := st.chat_input("Posez votre question..."):
    
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    
    with st.chat_message("assistant"):
        if not ollama_disponible:
            st.error("❌ Ollama n'est pas disponible. Installez-le depuis https://ollama.com puis lancez 'ollama pull mistral'")
        else:
            with st.spinner("Je réfléchis..."):
                reponse = repondre_avec_ollama(question, st.session_state.docs)
                st.markdown(reponse)
            
            st.session_state.messages.append({"role": "assistant", "content": reponse})

if not st.session_state.docs:
    st.info("""
    👋 **Bienvenue!**
    
    1. 📤 Uploadez vos documents (PDF ou TXT)
    2. 🔄 Cliquez sur "Charger les documents"
    3. 💬 Posez vos questions naturellement
    
    🆓 Utilise Ollama (100% gratuit, local)
    """)

st.markdown("---")
st.caption("Assistant IA conversationnel • Powered by Ollama (Gratuit)")