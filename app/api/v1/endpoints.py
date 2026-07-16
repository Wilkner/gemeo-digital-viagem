from typing import Union
from app.schemas.trip import (
    TripIngestInputSchema, 
    TripStoriesOutputSchema, 
    TripArticleOutputSchema
)
from app.schemas.persona import PersonaProfileSchema
from app.services.persona import PersonaService
from app.services.agents import StoriesAgent, ArticleAgent
from fastapi import File, UploadFile, APIRouter, HTTPException, status, Query
from app.services.media import MediaService
from google import genai
from pathlib import Path
import os

router = APIRouter()

# Caminho absoluto para a pasta de histórias estáticas
TRIPS_DIR = Path(__file__).resolve().parents[3] / "app" / "data" / "trips"

# Banco de dados temporário em memória para o MVP
trips_db = {}

@router.get("/persona", response_model=PersonaProfileSchema)
def get_active_persona():
    """
    Retorna o perfil ativo da Persona do Gêmeo Digital carregado do JSON.
    """
    try:
        return PersonaService.get_core_profile()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Erro ao carregar a Persona: {str(e)}"
        )

@router.get("/trips", status_code=status.HTTP_200_OK)
def list_available_trips():
    """
    Lista todas as histórias disponíveis na pasta 'app/data/trips/' lendo 
    o título real de dentro de cada arquivo Markdown/TXT.
    """
    if not TRIPS_DIR.exists():
        return []
        
    trips = []
    for file in TRIPS_DIR.glob("*.txt"):
        trip_id = file.stem  # Nome do arquivo (ex: 'david_michelangelo')
        display_title = trip_id.replace("_", " ").title()  # Fallback
        
        # Tenta ler a primeira linha ou a linha de título (# Título)
        try:
            with open(file, "r", encoding="utf-8") as f:
                for line in f:
                    clean_line = line.strip()
                    if clean_line.startswith("# "):
                        # Remove o '#' e espaços para pegar o título limpo
                        display_title = clean_line.lstrip("# ").strip()
                        break
        except Exception as e:
            print(f"Erro ao ler título do arquivo {file.name}: {str(e)}")
            
        trips.append({
            "trip_id": trip_id,
            "display_title": display_title
        })
    return trips


@router.get("/trips/{trip_id}/output")
def get_trip_output(trip_id: str, format: str):
    # Garante que o arquivo solicitado existe
    file_path = TRIPS_DIR / f"{trip_id}.txt"
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404, 
            detail=f"Crônica '{trip_id}' não encontrada no servidor."
        )
        
    try:
        # Lê o arquivo forçando o padrão universal UTF-8
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao ler o arquivo de crônica: {str(e)}"
        )

    # Aqui continua a lógica de geração ou leitura do seu JSON...

@router.post("/media/extract", status_code=status.HTTP_200_OK)
async def extract_media_metadata(file: UploadFile = File(...)):
    """
    Recebe um arquivo de imagem, valida se é um formato aceito, extrai os 
    metadados EXIF e usa o Gemini para geocodificação reversa.
    """
    # 1. Validação Rígida do Tipo de Arquivo (MIME Type)
    ALLOWED_TYPES = ["image/jpeg", "image/jpg"]
    
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato de arquivo inválido ({file.content_type}). Apenas imagens JPEG/JPG são permitidas para extração de EXIF."
        )
    
    # 2. Lê os bytes do arquivo enviado
    contents = await file.read()
    
    # 3. Extrai os metadados EXIF brutos
    metadata = MediaService.extract_exif(contents)
    
    # Se não encontrar dados EXIF básicos, retorna o que tem
    if not metadata["latitude"] or not metadata["longitude"]:
        return {
            "status": "success",
            "taken_at": metadata["taken_at"],
            "latitude": None,
            "longitude": None,
            "suggested_location": "Localização não encontrada nos metadados da imagem."
        }
        
    # 4. Geocodificação Reversa Inteligente com o Gemini 2.5 Flash
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            client = genai.Client(api_key=api_key)
            lat = metadata["latitude"]
            lon = metadata["longitude"]
            
            prompt = f"""
            Você é um assistente geográfico de precisão.
            Dadas as coordenadas geográficas Latitude: {lat} e Longitude: {lon}, identifique qual é o ponto de interesse turístico, museu, monumento histórico, praça ou estabelecimento de destaque que se localiza exatamente ou imediatamente próximo a este ponto.
            
            Responda EXCLUSIVAMENTE com o nome do local, seguido da cidade e país (ex: 'Galleria dell'Accademia, Florença, Itália'). Não adicione nenhuma introdução, explicação ou pontuação extra. Seja direto e preciso.
            """
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            metadata["suggested_location"] = response.text.strip()
        except Exception as e:
            metadata["suggested_location"] = f"Erro ao obter localização: {str(e)}"
    else:
        metadata["suggested_location"] = "Gemini API Key não configurada para geocodificação."
        
    return {
        "status": "success",
        "taken_at": metadata["taken_at"],
        "latitude": metadata["latitude"],
        "longitude": metadata["longitude"],
        "suggested_location": metadata["suggested_location"]
    }
        
    # 3. Geocodificação Reversa Inteligente com o Gemini 2.5 Flash
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            client = genai.Client(api_key=api_key)
            lat = metadata["latitude"]
            lon = metadata["longitude"]
            
            prompt = f"""
            Você é um assistente geográfico de precisão.
            Dadas as coordenadas geográficas Latitude: {lat} e Longitude: {lon}, identifique qual é o ponto de interesse turístico, museu, monumento histórico, praça ou estabelecimento de destaque que se localiza exatamente ou imediatamente próximo a este ponto.
            
            Responda EXCLUSIVAMENTE com o nome do local, seguido da cidade e país (ex: 'Galleria dell'Accademia, Florença, Itália'). Não adicione nenhuma introdução, explicação ou pontuação extra. Seja direto e preciso.
            """
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            metadata["suggested_location"] = response.text.strip()
        except Exception as e:
            metadata["suggested_location"] = f"Erro ao obter localização: {str(e)}"
    else:
        metadata["suggested_location"] = "Gemini API Key não configurada para geocodificação."
        
    return {
        "status": "success",
        "taken_at": metadata["taken_at"],
        "latitude": metadata["latitude"],
        "longitude": metadata["longitude"],
        "suggested_location": metadata["suggested_location"]
    }