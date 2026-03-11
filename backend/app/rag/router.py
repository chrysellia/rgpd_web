from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from app.auth.dependencies import get_current_user
from app.rag.query import query_agent, analyser_traitement
from app.database import get_db
from app.models import ChatHistory
import json
import pdfplumber
import PyPDF2
from io import BytesIO

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

@router.post("/chat-with-file")
async def chat_with_file(
    question: str = Form(...),
    domaine: str = Form("general"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Chat avec un fichier uploadé comme contexte supplémentaire."""

    # Lit le contenu du fichier
    content = await file.read()
    file_text = ""
    filename = file.filename.lower()

    try:
        # PDF
        if filename.endswith('.pdf'):
            try:
                with pdfplumber.open(BytesIO(content)) as pdf:
                    for page in pdf.pages:
                        file_text += page.extract_text() or ""
            except:
                pdf_reader = PyPDF2.PdfReader(BytesIO(content))
                for page in pdf_reader.pages:
                    file_text += page.extract_text() or ""

        # TXT
        elif filename.endswith('.txt'):
            file_text = content.decode('utf-8', errors='ignore')

        # CSV
        elif filename.endswith('.csv'):
            file_text = content.decode('utf-8', errors='ignore')

        else:
            raise HTTPException(
                status_code=400,
                detail="Format non supporté. Utilisez PDF, TXT ou CSV."
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lecture fichier: {str(e)}")

    if not file_text.strip():
        raise HTTPException(status_code=400, detail="Impossible d'extraire le texte du fichier.")

    # Limite le texte pour ne pas dépasser le contexte
    file_text_limite = file_text[:8000]

    # Enrichit la question avec le contenu du fichier
    question_enrichie = f"""L'utilisateur a partagé le document suivant :

--- CONTENU DU DOCUMENT : {file.filename} ---
{file_text_limite}
--- FIN DU DOCUMENT ---

Question de l'utilisateur : {question}

Analyse ce document dans le contexte RGPD et réponds à la question."""

    result = query_agent(question_enrichie, [], domaine)

    # Sauvegarde dans l'historique
    history_entry = ChatHistory(
        user_id=current_user.id,
        question=f"[Fichier: {file.filename}] {question}",
        answer=result["answer"],
        sources=json.dumps(result["sources"])
    )
    db.add(history_entry)
    db.commit()

    return {
        "question": question,
        "filename": file.filename,
        "answer": result["answer"],
        "sources": result["sources"]
    }