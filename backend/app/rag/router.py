from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.auth.dependencies import get_current_user
from app.rag.query import query_agent, analyser_traitement

router = APIRouter()

class QuestionRequest(BaseModel):
    question: str
    historique: Optional[List[dict]] = []

class TraitementRequest(BaseModel):
    nom: str
    finalite: str
    base_legale: str
    categories_donnees: str
    destinataires: str
    duree_conservation: str
    transferts_hors_ue: bool = False

@router.post("/chat")
def chat(
    req: QuestionRequest,
    current_user=Depends(get_current_user)
):
    """Endpoint principal de chat avec l'agent RGPD."""
    result = query_agent(req.question, req.historique)
    return {
        "question": req.question,
        "answer": result["answer"],
        "sources": result["sources"],
        "user": current_user.email
    }

@router.post("/analyser-traitement")
def analyser(
    traitement: TraitementRequest,
    current_user=Depends(get_current_user)
):
    """Analyse un traitement de données et retourne des recommandations."""
    result = analyser_traitement(traitement.dict())
    return {
        "analyse": result["answer"],
        "sources": result["sources"],
        "traitement": traitement.dict()
    }

@router.get("/status")
def status():
    """Vérifie si la base vectorielle est prête."""
    import os
    chroma_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    return {
        "vectorstore_ready": os.path.exists(chroma_path),
        "ollama_model": os.getenv("OLLAMA_MODEL", "mistral")
    }