from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from app.auth.dependencies import get_current_user
from app.rag.query import query_agent, analyser_traitement
from app.database import get_db
from app.models import ChatHistory
import json

router = APIRouter()

class QuestionRequest(BaseModel):
    question: str
    historique: Optional[List[dict]] = []
    domaine: Optional[str] = "general"

class TraitementRequest(BaseModel):
    nom: str
    finalite: str
    base_legale: str
    categories_donnees: str
    destinataires: str
    duree_conservation: str
    transferts_hors_ue: bool = False
    domaine: Optional[str] = "general"

@router.post("/chat")
def chat(
    req: QuestionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    result = query_agent(req.question, req.historique, req.domaine)

    # Sauvegarde dans l'historique
    history_entry = ChatHistory(
        user_id=current_user.id,
        question=req.question,
        answer=result["answer"],
        sources=json.dumps(result["sources"])
    )
    db.add(history_entry)
    db.commit()

    return {
        "question": req.question,
        "answer": result["answer"],
        "sources": result["sources"],
        "user": current_user.email
    }

@router.get("/historique")
def get_historique(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    history = db.query(ChatHistory)\
                .filter(ChatHistory.user_id == current_user.id)\
                .order_by(ChatHistory.created_at.desc())\
                .limit(50).all()

    return [
        {
            "id": h.id,
            "question": h.question,
            "answer": h.answer,
            "sources": json.loads(h.sources) if h.sources else [],
            "created_at": h.created_at.isoformat()
        }
        for h in history
    ]

@router.post("/analyser-traitement")
def analyser(
    traitement: TraitementRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    result = analyser_traitement(traitement.dict())
    return {
        "analyse": result["answer"],
        "sources": result["sources"],
        "traitement": traitement.dict()
    }

@router.get("/status")
def status():
    import os
    chroma_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    return {
        "vectorstore_ready": os.path.exists(chroma_path),
        "ollama_model": os.getenv("OLLAMA_MODEL", "mistral")
    }