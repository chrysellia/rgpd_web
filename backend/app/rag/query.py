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

# Contextes par domaine
DOMAINE_CONTEXTES = {
    "sante": """Tu assistes un DPO dans le secteur SANTÉ/MÉDICAL.
    Les données sensibles incluent : données de santé, numéro de sécurité sociale,
    antécédents médicaux, traitements, résultats d'analyses.
    Base légale souvent utilisée : obligation légale, intérêt vital, mission de santé publique.
    Durées de conservation spécifiques : dossier médical 20 ans minimum.""",

    "rh": """Tu assistes un DPO dans les RESSOURCES HUMAINES.
    Les données traitées incluent : nom, prénom, CV, salaire, évaluations,
    coordonnées bancaires, absences, données disciplinaires.
    Base légale : contrat de travail, obligation légale.
    Durées : données paie 5 ans, dossier salarié 5 ans après départ.""",

    "education": """Tu assistes un DPO dans le secteur ÉDUCATION.
    Les données incluent : données d'élèves mineurs, résultats scolaires,
    données parents, données enseignants.
    Attention particulière aux données de mineurs — protection renforcée.""",

    "finance": """Tu assistes un DPO dans le secteur FINANCE/BANQUE.
    Les données incluent : IBAN, revenus, historique transactions,
    données de crédit, données KYC.
    Base légale : obligation légale (LCB-FT), contrat.
    Durées : données bancaires 5 à 10 ans selon type.""",

    "commerce": """Tu assistes un DPO dans le secteur COMMERCE/E-COMMERCE.
    Les données incluent : données clients, historique achats,
    données de paiement, cookies, données de navigation.
    Base légale : consentement, contrat, intérêt légitime.""",

    "juridique": """Tu assistes un DPO dans le secteur JURIDIQUE.
    Les données incluent : données clients, pièces judiciaires,
    données sensibles liées aux affaires.
    Secret professionnel et confidentialité renforcés.""",

    "industrie": """Tu assistes un DPO dans le secteur INDUSTRIEL.
    Les données incluent : données employés, données fournisseurs,
    données de contrôle d'accès, vidéosurveillance.""",

    "general": """Tu assistes un DPO dans une organisation."""
}

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

def query_agent(question: str, historique: list = [], domaine: str = "general") -> dict:
    if not os.path.exists(CHROMA_DB_PATH):
        return {
            "answer": "Base documentaire non initialisée.",
            "sources": []
        }

    vectorstore = get_vectorstore()
    docs_pertinents = vectorstore.similarity_search(question, k=5)

    if not docs_pertinents:
        return {
            "answer": "Aucun document pertinent trouvé. Reformulez votre question.",
            "sources": []
        }

    contexte = "\n\n".join([
        f"[Source: {doc.metadata.get('source', 'Document RGPD')}]\n{doc.page_content}"
        for doc in docs_pertinents
    ])

    sources = list(set([
        os.path.basename(doc.metadata.get('source', 'Document inconnu'))
        for doc in docs_pertinents
    ]))

    # Contexte domaine
    domaine_context = DOMAINE_CONTEXTES.get(domaine, DOMAINE_CONTEXTES["general"])

    # Historique formaté
    historique_formate = ""
    if historique:
        for msg in historique[-4:]:  # 4 derniers messages
            role = "Utilisateur" if msg.get("role") == "user" else "Assistant"
            historique_formate += f"{role}: {msg.get('content', '')}\n"

    prompt = f"""Tu es un assistant expert en conformité RGPD.
{domaine_context}

INSTRUCTIONS :
- Réponds de façon précise, structurée et professionnelle
- Si l'utilisateur demande quelles données saisir pour un champ, 
  donne des exemples concrets adaptés à son domaine
- Si l'utilisateur demande la base légale, explique les options disponibles
- Si l'utilisateur demande la durée de conservation, donne des durées précises
- Cite toujours les articles RGPD pertinents quand c'est possible
- Réponds toujours en français

DOCUMENTS DE RÉFÉRENCE :
{contexte}

HISTORIQUE DE LA CONVERSATION :
{historique_formate}

QUESTION ACTUELLE : {question}

RÉPONSE :"""

    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        answer = response['message']['content']
    except Exception as e:
        answer = f"Erreur : {str(e)}"

    return {
        "answer": answer,
        "sources": sources
    }

def analyser_traitement(traitement_data: dict) -> dict:
    domaine = traitement_data.get('domaine', 'general')
    question = f"""Analyse ce traitement de données et vérifie sa conformité RGPD.
    Identifie les risques, vérifie la base légale, et donne des recommandations précises.

    Traitement :
    - Nom : {traitement_data.get('nom', 'Non renseigné')}
    - Finalité : {traitement_data.get('finalite', 'Non renseigné')}
    - Base légale : {traitement_data.get('base_legale', 'Non renseigné')}
    - Catégories de données : {traitement_data.get('categories_donnees', 'Non renseigné')}
    - Destinataires : {traitement_data.get('destinataires', 'Non renseigné')}
    - Durée de conservation : {traitement_data.get('duree_conservation', 'Non renseigné')}
    - Transferts hors UE : {traitement_data.get('transferts_hors_ue', 'Non')}
    """
    return query_agent(question, domaine=domaine)