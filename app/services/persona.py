import json
import os
from app.schemas.persona import PersonaProfileSchema

class PersonaService:
    @staticmethod
    def get_core_profile() -> PersonaProfileSchema:
        # Define o caminho do arquivo JSON de forma segura
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(base_dir, "data", "persona_profile.json")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo de perfil não encontrado em: {file_path}")
            
        with open(file_path, "r", encoding="utf-8") as file:
            profile_data = json.load(file)
            
        # Valida os dados brutos usando o schema do Pydantic
        return PersonaProfileSchema(**profile_data)