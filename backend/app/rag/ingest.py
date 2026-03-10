"""
Lance ce script UNE FOIS pour indexer tes PDFs RGPD.
Commande : python app/rag/ingest.py
"""
import os
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv

load_dotenv()

DOCUMENTS_PATH = os.getenv("DOCUMENTS_PATH", "./documents")
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

def ingest_documents():
    print("Chargement des documents RGPD...")

    # Charge tous les PDFs du dossier documents/
    loader = DirectoryLoader(
        DOCUMENTS_PATH,
        glob="**/*.pdf",
        loader_cls=PyPDFLoader
    )
    documents = loader.load()

    if not documents:
        print("ERREUR : Aucun PDF trouvé dans", DOCUMENTS_PATH)
        return 0

    print(f"{len(documents)} pages chargées")

    # Découpe en fragments de 512 tokens
    # avec chevauchement de 50 tokens pour préserver le contexte
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " "]
    )
    chunks = splitter.split_documents(documents)
    print(f"{len(chunks)} fragments créés")

    # Vectorise avec Ollama (modèle local)
    print("Vectorisation en cours (peut prendre quelques minutes)...")
    embeddings = OllamaEmbeddings(
        model=OLLAMA_MODEL,
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    )

    # Stocke dans ChromaDB
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DB_PATH,
        collection_name="rgpd_docs"
    )

    print(f"✅ {len(chunks)} fragments indexés dans ChromaDB")
    print(f"Base vectorielle sauvegardée dans : {CHROMA_DB_PATH}")
    return len(chunks)

if __name__ == "__main__":
    ingest_documents()