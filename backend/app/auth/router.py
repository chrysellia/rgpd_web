from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.auth.service import hash_password, verify_password, create_access_token
from pydantic import BaseModel
import secrets
from datetime import datetime, timedelta

router = APIRouter()

class RegisterRequest(BaseModel):
    email: str
    password: str

@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email deja utilise")
    user = User(email=req.email, hashed_password=hash_password(req.password))
    db.add(user)
    db.commit()
    return {"message": "Compte cree avec succes"}

@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Identifiants incorrects")
    token = create_access_token({"sub": user.email})
    return {
        "token": token,
        "access_token": token,
        "token_type": "bearer",
        "expiresIn": 3600,
        "refreshToken": token,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "firstName": "Utilisateur",
            "lastName": "RGPD",
            "role": user.role,
            "createdAt": user.created_at.isoformat(),
            "lastLoginAt": None,
            "isActive": user.is_active
        }
    }

@router.get("/me")
def get_me(db: Session = Depends(get_db)):
    return {"message": "endpoint me"}

# Stockage temporaire des tokens de reset (en production utilise Redis)
reset_tokens = {}

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    
    # On retourne toujours le même message pour éviter l'énumération d'emails
    if not user:
        return {"message": "Si cet email existe, un lien de réinitialisation a été envoyé."}
    
    # Génère un token temporaire valable 1 heure
    token = secrets.token_urlsafe(32)
    reset_tokens[token] = {
        "email": req.email,
        "expires_at": datetime.utcnow() + timedelta(hours=1)
    }
    
    # En production : envoie un email avec ce token
    # Pour le développement : on retourne le token directement
    return {
        "message": "Token de réinitialisation généré.",
        "reset_token": token,  # ← retirer en production
        "expires_in": "1 heure"
    }

@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    # Vérifie le token
    token_data = reset_tokens.get(req.token)
    if not token_data:
        raise HTTPException(status_code=400, detail="Token invalide ou expiré.")
    
    if datetime.utcnow() > token_data["expires_at"]:
        del reset_tokens[req.token]
        raise HTTPException(status_code=400, detail="Token expiré.")
    
    # Met à jour le mot de passe
    user = db.query(User).filter(User.email == token_data["email"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    
    user.hashed_password = hash_password(req.new_password)
    db.commit()
    
    # Supprime le token utilisé
    del reset_tokens[req.token]
    
    return {"message": "Mot de passe réinitialisé avec succès."}