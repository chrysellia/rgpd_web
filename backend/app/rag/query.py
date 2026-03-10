# Pipeline de requête

import os
import ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv

load_dotenv()

CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

def get_vectorstore():
    embeddings = OllamaEmbeddings(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL
    )
    return Chroma(
        persist_directory=CHROMA_DB_PATH,
        embedding_function=embeddings,
        collection_name="rgpd_docs"
    )

def query_agent(question: str, historique: list = []) -> dict:
    """
    Pipeline RAG complet :
    1. Recherche les passages pertinents dans ChromaDB
    2. Construit le prompt avec contexte
    3. Appelle Mistral via Ollama
    4. Retourne la réponse + sources
    """
    # Vérifie que la base vectorielle existe
    if not os.path.exists(CHROMA_DB_PATH):
        return {
            "answer": "Base documentaire non initialisée. Lancez d'abord l'ingestion des documents.",
            "sources": []
        }

    # Recherche les 5 passages les plus pertinents
    vectorstore = get_vectorstore()
    docs_pertinents = vectorstore.similarity_search(question, k=5)

    if not docs_pertinents:
        return {
            "answer": "Aucun document pertinent trouvé pour cette question.",
            "sources": []
        }

    # Construit le contexte à partir des passages retrouvés
    contexte = "\n\n".join([
        f"[Source: {doc.metadata.get('source', 'Document RGPD')}]\n{doc.page_content}"
        for doc in docs_pertinents
    ])

    # Sources uniques pour la réponse
    sources = list(set([
        os.path.basename(doc.metadata.get('source', 'Document inconnu'))
        for doc in docs_pertinents
    ]))

    # Construit le prompt
    prompt = f"""Tu es un assistant expert en conformité RGPD au sein d'une organisation.
Tu réponds uniquement en te basant sur les documents fournis.
Si la réponse ne figure pas dans les documents, dis-le clairement et poliment.
Réponds de façon structurée, professionnelle et en français.

DOCUMENTS DE RÉFÉRENCE :
{contexte}

QUESTION : {question}

RÉPONSE :"""

    # Appel à Ollama (Mistral local)
    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        answer = response['message']['content']
    except Exception as e:
        answer = f"Erreur lors de la génération : {str(e)}"

    return {
        "answer": answer,
        "sources": sources
    }

def analyser_traitement(traitement_data: dict) -> dict:
    """
    Analyse un formulaire de traitement RGPD
    et retourne des recommandations.
    """
    question = f"""Analyse ce traitement de données personnelles et vérifie
    sa conformité RGPD. Identifie les risques et donne des recommandations.

    Traitement à analyser :
    - Nom : {traitement_data.get('nom', 'Non renseigné')}
    - Finalité : {traitement_data.get('finalite', 'Non renseigné')}
    - Base légale : {traitement_data.get('base_legale', 'Non renseigné')}
    - Catégories de données : {traitement_data.get('categories_donnees', 'Non renseigné')}
    - Destinataires : {traitement_data.get('destinataires', 'Non renseigné')}
    - Durée de conservation : {traitement_data.get('duree_conservation', 'Non renseigné')}
    - Transferts hors UE : {traitement_data.get('transferts_hors_ue', 'Non')}
    """

    return query_agent(question)