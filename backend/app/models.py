from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users_rgpd"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="dpo")  # dpo, charge_traitement, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

class Traitement(Base):
    __tablename__ = "traitements"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    nom = Column(String)
    finalite = Column(Text)
    base_legale = Column(String)
    categories_donnees = Column(Text)
    destinataires = Column(Text)
    duree_conservation = Column(String)
    transferts_hors_ue = Column(Boolean, default=False)
    analyse_rgpd = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    question = Column(Text)
    answer = Column(Text)
    sources = Column(Text)
    created_at = Column(DateTime, server_default=func.now())