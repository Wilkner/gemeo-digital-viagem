from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.endpoints import router as api_v1_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Engine assíncrona para transformação de mídias e relatos de viagem usando GenAI.",
    version=settings.PROJECT_VERSION
)

# Configuração de CORS para permitir conexões locais da IDE e do Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui as rotas com o prefixo da API V1 (/api/v1)
app.include_router(api_v1_router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {
        "status": "Gêmeo Digital Core Online",
        "mode": "Antigravity Active",
        "docs": "/docs"
    }
