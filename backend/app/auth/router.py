from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.auth.service import hash_password, verify_password, create_access_token
from pydantic import BaseModel

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