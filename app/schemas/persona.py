from pydantic import BaseModel, Field
from typing import List

class PersonaProfileSchema(BaseModel):
    name: str = Field(..., description="Nome da persona do viajante")
    tone: str = Field(..., description="Tom de voz da persona")
    slangs: List[str] = Field(default_factory=list, description="Lista de gírias preferidas")
    avoided_words: List[str] = Field(default_factory=list, description="Palavras ou jargões a serem evitados")
    writing_style: str = Field(..., description="Descrição detalhada do estilo de escrita")
