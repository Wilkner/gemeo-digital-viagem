from pydantic import BaseModel, Field
from typing import List, Optional, Union
from datetime import datetime

# =====================================================================
# 1. Schemas para o formato de Instagram Stories (RFC-001 / RFC-003)
# =====================================================================

class EngagementStickerSchema(BaseModel):
    type: str = Field(..., description="Tipo de sticker: poll, question ou none")
    question: Optional[str] = Field(None, description="Pergunta do sticker, se aplicável")
    options: Optional[List[str]] = Field(None, description="Opções de resposta para enquetes")

class StoryFrameSchema(BaseModel):
    frame_number: int
    layout_type: str = Field(..., description="text_over_image, video_prompt ou poll")
    visual_direction: str = Field(..., description="Direção visual detalhada para a tela")
    overlay_text: str = Field(..., description="Texto de impacto com limite de 150 caracteres")
    audio_suggestion: str = Field(..., description="Música ou áudio sugerido para o fundo")
    engagement_sticker: EngagementStickerSchema

class TripStoriesOutputSchema(BaseModel):
    trip_id: str
    format: str = "instagram_stories"
    generated_at: datetime
    stories_sequence: List[StoryFrameSchema]


# =====================================================================
# 2. Schemas para o formato de Artigo Detalhado em Markdown (RFC-004)
# =====================================================================

class TripArticleOutputSchema(BaseModel):
    trip_id: str
    format: str = "article"
    generated_at: datetime
    title: str = Field(..., description="Um título impactante, poético e nada clichê")
    subtitle: str = Field(..., description="Subtítulo reflexivo que resume a essência da experiência")
    content_markdown: str = Field(..., description="Texto completo formatado usando Markdown estruturado")
    suggested_reading_time_minutes: int = Field(..., description="Tempo de leitura estimado em minutos")


# =====================================================================
# 3. Schemas de Ingestão de Viagem (Camada de Entrada)
# =====================================================================

class MediaMetadataSchema(BaseModel):
    media_id: str
    timestamp: datetime
    detected_objects: List[str]
    user_notes: Optional[str] = None

class TripIngestInputSchema(BaseModel):
    user_id: str
    trip_id: str
    raw_text: str
    media_metadata: List[MediaMetadataSchema] = Field(default_factory=list)


# Schema utilitário para respostas dinâmicas na API
class TripOutputResponse(BaseModel):
    output: Union[TripStoriesOutputSchema, TripArticleOutputSchema]