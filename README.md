# Agent RGPD Web — Plateforme de Conformité Intelligente

> Module web de la plateforme d'agents IA spécialisés pour la conformité RGPD au sein du système d'information.

---

## Présentation

L'Agent RGPD est une application web qui permet aux équipes métiers (DPO, chargés de traitement) de :

- Poser des questions sur la conformité RGPD en langage naturel
- Obtenir des réponses contextualisées selon leur domaine d'activité
- Analyser des traitements de données et vérifier leur conformité
- Importer des documents PDF/TXT pour analyse RGPD
- Consulter l'historique des conversations
- Bénéficier d'un agent IA entièrement local (aucune donnée ne quitte l'organisation)

---

## Architecture

```
rgpd_web/
├── backend/          ← API FastAPI + Pipeline RAG
│   ├── app/
│   │   ├── auth/     ← Authentification JWT
│   │   └── rag/      ← Pipeline RAG (ChromaDB + Ollama)
│   ├── documents/    ← PDFs RGPD à indexer
│   └── chroma_db/    ← Base vectorielle (généré automatiquement)
└── frontend/         ← Interface React + Tailwind CSS
    └── src/
        ├── pages/    ← Login, Dashboard, Chat, Traitement
        ├── components/
        └── services/ ← Connexion API
```

---

## Prérequis

- Python 3.11+
- Node.js 20+
- PostgreSQL 14+
- [Ollama](https://ollama.com) avec le modèle Mistral

```bash
# Installe Mistral via Ollama
ollama pull mistral
```

---

## Installation

### 1. Clone le repository

```bash
git clone https://github.com/chrysellia/rgpd-web.git
cd rgpd-web
```

### 2. Configure le backend

```bash
cd backend

# Crée l'environnement virtuel
python -m venv venv

# Active-le
# Windows :
.\venv\Scripts\activate
# Linux/Mac :
source venv/bin/activate

# Installe les dépendances
pip install fastapi uvicorn "python-jose[cryptography]" passlib bcrypt==4.0.1 \
    passlib==1.7.4 python-multipart sqlalchemy psycopg2-binary python-dotenv \
    langchain langchain-community langchain-text-splitters chromadb ollama \
    pdfplumber PyPDF2
```

### 3. Configure les variables d'environnement

Crée un fichier `.env` dans `backend/` en te basant sur `.env.example` :

```env
DATABASE_URL=postgresql://postgres:TonMotDePasse@localhost:5432/rgpd_db
SECRET_KEY=ta_cle_secrete_jwt_longue_ici
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
CHROMA_DB_PATH=./chroma_db
DOCUMENTS_PATH=./documents
```

### 4. Crée la base de données

Dans pgAdmin, ouvre l'éditeur SQL et exécute :

```sql
CREATE DATABASE rgpd_db;

CREATE TABLE IF NOT EXISTS users_rgpd (
    id SERIAL PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL,
    role VARCHAR DEFAULT 'dpo',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS traitements (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    nom VARCHAR,
    finalite TEXT,
    base_legale VARCHAR,
    categories_donnees TEXT,
    destinataires TEXT,
    duree_conservation VARCHAR,
    transferts_hors_ue BOOLEAN DEFAULT FALSE,
    analyse_rgpd TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chat_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    question TEXT,
    answer TEXT,
    sources TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 5. Indexe tes documents RGPD

Place tes fichiers PDF dans `backend/documents/` puis lance :

```bash
python app/rag/ingest.py
```

Tu verras :
```
X pages chargées
X fragments créés
✅ X fragments indexés dans ChromaDB
```

### 6. Configure le frontend

```bash
cd ../frontend

# Installe les dépendances
npm install

# Installe Tailwind CSS v3
npm install -D tailwindcss@3 postcss autoprefixer
```

---

## Lancement

Lance les deux serveurs dans deux terminaux séparés :

```bash
# Terminal 1 — Backend (depuis backend/)
.\venv\Scripts\activate
python -m uvicorn main:app --reload --port 8001

# Terminal 2 — Frontend (depuis frontend/)
npm run dev
```

Accès :
- **Application** : http://localhost:5173
- **API Swagger** : http://localhost:8001/docs

---

## Utilisation

### Créer un compte

Sur `http://localhost:8001/docs` → `POST /auth/register` :

```json
{
  "email": "dpo@entreprise.com",
  "password": "VotreMotDePasse"
}
```

### Fonctionnalités disponibles

**Chat avec l'agent RGPD**
- Sélectionnez votre domaine d'activité (Santé, RH, Finance, etc.)
- Posez vos questions en langage naturel
- Joignez un fichier PDF/TXT pour analyse
- Consultez l'historique de vos conversations

**Analyse de traitement**
- Remplissez le formulaire avec les informations du traitement
- L'agent analyse automatiquement la conformité RGPD
- Recevez des recommandations et identifiez les risques

---

## Domaines supportés

| Domaine | Données typiques |
|---|---|
| Général | Toutes organisations |
| Santé | Données médicales, dossiers patients |
| RH | Données employés, paie, évaluations |
| Éducation | Données élèves, résultats scolaires |
| Finance | IBAN, KYC, transactions |
| Commerce | Données clients, cookies, paiements |
| Juridique | Données confidentielles, pièces judiciaires |
| Industrie | Contrôle d'accès, vidéosurveillance |

---

## Stack technique

| Composant | Technologie |
|---|---|
| Backend API | FastAPI (Python) |
| Base de données | PostgreSQL |
| Agent RAG | LangChain + ChromaDB |
| Modèle LLM | Ollama + Mistral (local) |
| Authentification | JWT (python-jose) |
| Frontend | React + Vite |
| Style | Tailwind CSS v3 |
| Icônes | Lucide React |

---

## Sécurité

- Toutes les données restent **en local** — aucun envoi vers des services cloud
- Authentification JWT avec expiration configurable
- Mots de passe hashés avec bcrypt
- Le fichier `.env` est exclu du versioning (`.gitignore`)

---

## Structure des fichiers importants

```
backend/
├── main.py                  ← Point d'entrée FastAPI
├── .env                     ← Variables d'environnement (non versionné)
├── .env.example             ← Template sans secrets
├── app/
│   ├── auth/
│   │   ├── router.py        ← Endpoints login/register
│   │   ├── service.py       ← Logique JWT + hash
│   │   └── dependencies.py  ← Middleware authentification
│   └── rag/
│       ├── router.py        ← Endpoints chat/analyse
│       ├── ingest.py        ← Indexation des PDFs
│       └── query.py         ← Pipeline RAG + prompts par domaine
frontend/
├── src/
│   ├── pages/
│   │   ├── LoginPage.jsx
│   │   ├── DashboardPage.jsx
│   │   ├── ChatPage.jsx     ← Chat + import fichiers + historique
│   │   └── TraitementPage.jsx
│   ├── components/
│   │   ├── Navbar.jsx
│   │   └── ProtectedRoute.jsx
│   └── services/
│       └── api.js           ← Appels API avec JWT automatique
```

---

## Auteur

Projet réalisé dans le cadre d'un mémoire de Master :
**"Conception d'agents d'intelligence artificielle spécialisés et sécurisés au sein du système d'information"**