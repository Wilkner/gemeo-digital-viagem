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
import json
# Importe as suas funções de geração e caminhos de diretórios existentes
# Exemplo:
from app.services.agents import ArticleAgent, StoriesAgent

# Calcula o caminho absoluto para a pasta de crônicas (app/data/trips)
# Isso garante que funcione tanto no Windows do seu PC quanto no Linux do Render!
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent # Sobe até a raiz do projeto
TRIPS_DIR = BASE_DIR / "app" / "data" / "trips"

# Garante que a pasta exista (se não existir, ele cria de forma automática)
TRIPS_DIR.mkdir(parents=True, exist_ok=True)

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
    o título, a data de inclusão e o destino de dentro de cada arquivo TXT.
    Retorna a lista ordenada pela data mais recente.
    """
    if not TRIPS_DIR.exists():
        return []
        
    trips = []
    for file in TRIPS_DIR.glob("*.txt"):
        trip_id = file.stem  # Nome do arquivo (ex: 'david_michelangelo')
        display_title = trip_id.replace("_", " ").title()  # Fallback
        trip_date = "2026-01-01"  # Data padrão caso não encontre
        destination = "Geral"  # Destino padrão caso não encontre
        
        try:
            with open(file, "r", encoding="utf-8") as f:
                for line in f:
                    clean_line = line.strip()
                    # Lê metadados de data
                    if clean_line.lower().startswith("date:"):
                        trip_date = clean_line.split(":", 1)[1].strip()
                    # Lê metadados de destino
                    elif clean_line.lower().startswith("destination:"):
                        destination = clean_line.split(":", 1)[1].strip()
                    # Lê o título principal
                    elif clean_line.startswith("# "):
                        display_title = clean_line.lstrip("# ").strip()
        except Exception as e:
            print(f"Erro ao ler metadados do arquivo {file.name}: {str(e)}")
            
        trips.append({
            "trip_id": trip_id,
            "display_title": display_title,
            "date": trip_date,
            "destination": destination
        })
    
    # ORDENAÇÃO: Ordena a lista de viagens da data mais recente para a mais antiga
    trips.sort(key=lambda x: x["date"], reverse=True)
    
    return trips


@router.get("/trips/{trip_id}/output")
def get_trip_output(
    trip_id: str, 
    format: str = Query(..., description="Formatos: 'article' ou 'stories'"),
    mode: str = Query("coauthor", description="Modo de geração")
):
    # 1. Monta os caminhos físicos dos arquivos
    txt_file = TRIPS_DIR / f"{trip_id}.txt"
    cache_json_file = TRIPS_DIR / f"{trip_id}_{format}.json"

    # Verificação de segurança: o relato bruto original .txt existe?
    if not txt_file.exists():
        raise HTTPException(
            status_code=404, 
            detail=f"O relato original '{trip_id}.txt' não foi encontrado no servidor."
        )

    # 2. FLUXO DE CACHE: Se o JSON gerado anteriormente já existe, servimos ele direto!
    if cache_json_file.exists():
        try:
            with open(cache_json_file, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
                print(f"⚡ [CACHE HIT] Retornando dados estáticos para {trip_id} ({format})")
                return cached_data
        except Exception as e:
            # Se o arquivo de cache estiver corrompido, ignoramos e geramos de novo
            print(f"⚠️ Erro ao ler arquivo de cache: {e}. Gerando novamente...")

    # 3. GERAR COM IA (Se não houver cache)
    print(f"🤖 [CACHE MISS] Chamando a API do Gemini para gerar {trip_id} ({format})...")
    
    output_data = None
    
    try:
        # Lê o seu arquivo bruto .txt
        with open(txt_file, "r", encoding="utf-8") as f:
            raw_text = f.read()

        # Usamos o serviço de persona oficial do seu projeto que já está importado no topo!
        persona = PersonaService.get_core_profile()

        # Roda o agente correspondente acessando o método estático da classe
        if format == "stories":
            output_data = StoriesAgent.generate_stories(raw_text=raw_text, persona=persona, trip_id=trip_id)
        else:
            output_data = ArticleAgent.generate_article(raw_text=raw_text, persona=persona, trip_id=trip_id, mode=mode)

        if not output_data:
            raise ValueError("A função do agente retornou vazia ou None")

    except Exception as e:
        print(f"❌ [ERRO NA GERAÇÃO DA IA]: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro durante a geração ou parse da IA: {str(e)}"
        )

    # 4. SALVAR EM CACHE: Grava o JSON gerado no disco para as próximas requisições
    try:
        caminho_arquivo = Path(cache_json_file)
        with open(caminho_arquivo, "w", encoding="utf-8") as f:
            if isinstance(output_data, str):
                f.write(output_data)
            else:
                # ─── TRATAMENTO DE SERIALIZAÇÃO SEGURO COM PYDANTIC V2 ───
                # O parâmetro mode="json" força o Pydantic a converter datetimes para strings ISO-8601 automaticamente!
                if hasattr(output_data, "model_dump"):
                    dados_para_salvar = output_data.model_dump(mode="json")
                elif hasattr(output_data, "dict"):
                    # Fallback para Pydantic V1 (usando serialização via FastAPI jsonable_encoder)
                    from fastapi.encoders import jsonable_encoder
                    dados_para_salvar = jsonable_encoder(output_data)
                else:
                    dados_para_salvar = output_data
                
                json.dump(dados_para_salvar, f, ensure_ascii=False, indent=4)
        
        nome_amigavel = os.path.basename(str(cache_json_file))
        print(f"💾 [CACHE GUARDADO] Arquivo {nome_amigavel} salvo com sucesso.")
    except Exception as e:
        print(f"⚠️ Erro ao salvar o arquivo de cache físico: {str(e)}")

    # Retorna o resultado gerado para o frontend
    return output_data
    
    try:
        # Lê o seu arquivo bruto .txt
        with open(txt_file, "r", encoding="utf-8") as f:
            raw_text = f.read()

        # ─── CARREGAR A PERSONA (Ajuste conforme a arquitetura do seu projeto) ───
        # O seu projeto provavelmente importa a Persona do Core Profile estático.
        # Caso você tenha um arquivo 'persona.json' ou utilize o serviço de persona:
        try:
            # Tenta carregar usando as classes de serviço se você as tiver importado
            from app.services.persona import PersonaEngine
            persona = PersonaEngine.get_active_persona() # Ou método equivalente do seu projeto
        except Exception:
            # Fallback seguro caso o projeto use o Schema instanciado de forma básica:
            from app.schemas.trip import PersonaProfileSchema # Ajuste o caminho do import do Schema se necessário
            # Instancia um objeto vazio/padrão de persona para a chamada não quebrar por falta de definição
            persona = PersonaProfileSchema(
                name="Wilkner",
                writing_style="journalistic",
                tone="informal",
                slangs=[],
                avoid_topics=[]
            )

        # Roda o agente correspondente acessando o método estático da classe
        if format == "stories":
            output_data = StoriesAgent.generate_stories(raw_text=raw_text, persona=persona, trip_id=trip_id)
        else:
            output_data = ArticleAgent.generate_article(raw_text=raw_text, persona=persona, trip_id=trip_id, mode=mode)

        if not output_data:
            raise ValueError("A função do agente retornou vazia ou None")

    except Exception as e:
        print(f"❌ [ERRO NA GERAÇÃO DA IA]: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro durante a geração ou parse da IA: {str(e)}"
        )

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