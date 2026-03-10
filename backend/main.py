from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth.router import router as auth_router
from app.rag.router import router as rag_router

app = FastAPI(title="Agent RGPD API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(rag_router, prefix="/rgpd", tags=["RGPD"])

@app.get("/")
def root():
    return {"status": "Agent RGPD API running"}