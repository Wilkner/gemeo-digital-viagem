import os
from datetime import datetime, timezone
from google import genai
from google.genai import types
from dotenv import load_dotenv

from app.schemas.trip import TripStoriesOutputSchema, TripArticleOutputSchema
from app.schemas.persona import PersonaProfileSchema

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

class StoriesAgent:
    @staticmethod
    def generate_stories(raw_text: str, persona: PersonaProfileSchema, trip_id: str) -> TripStoriesOutputSchema:
        """
        Gera a sequência de Stories estruturada a partir do relato bruto (RFC-001/RFC-003).
        """
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("A variável de ambiente GEMINI_API_KEY não foi configurada no arquivo .env")
            
        client = genai.Client(api_key=api_key)
        
        system_instruction = f"""
        Você é o Gêmeo Digital de {persona.name}. Você escreve exatamente no estilo dele.
        
        Suas características absolutas de escrita:
        - Tom de voz: {persona.tone}
        - Estilo de escrita: {persona.writing_style}
        - Gírias que você ADORA usar: {persona.slangs}
        - Palavras ou expressões que você NUNCA deve usar de jeito nenhum: {persona.avoided_words}
        
        Sua Missão:
        Transformar o relato bruto de viagem fornecido pelo usuário em uma narrativa sequencial de Stories para o Instagram (máximo de 6 telas).
        
        Diretrizes do Formato (Stories):
        1. Tela 1 (O Gancho): Deve prender a atenção imediata, gerando curiosidade profunda ou quebrando expectativa.
        2. Telas Intermediárias: Desenvolvem a crônica de forma dinâmica. Frases curtas, ritmo rápido.
        3. Tela Final (Engajamento): Deve terminar com uma pergunta instigante ou enquete para o público interagir.
        
        Restrições Críticas:
        - O campo 'overlay_text' de cada tela não pode passar de 150 caracteres.
        - Jamais use clichês corporativos ou transições artificiais.
        """

        user_prompt = f"Aqui está o meu relato bruto para os Stories:\n\n{raw_text}"
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
                response_mime_type="application/json",
                response_schema=TripStoriesOutputSchema,
            ),
        )
        
        try:
            output = TripStoriesOutputSchema.model_validate_json(response.text)
            output.trip_id = trip_id
            output.generated_at = datetime.now(timezone.utc)
            return output
        except Exception as e:
            raise RuntimeError(f"Falha ao mapear Stories: {str(e)}. Resposta: {response.text}")


class ArticleAgent:
    @staticmethod
    def generate_article(
        raw_text: str, 
        persona: PersonaProfileSchema, 
        trip_id: str, 
        mode: str = "coauthor"
    ) -> TripArticleOutputSchema:
        """
        Gera uma crônica de viagem formatada em Markdown a partir do relato bruto (RFC-004/RFC-005).
        Suporta o modo 'coauthor' (preserva texto original) e 'ghostwriter' (reescreve com IA).
        """
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("A variável de ambiente GEMINI_API_KEY não foi configurada no arquivo .env")
            
        client = genai.Client(api_key=api_key)
        
        # Ajustamos dinamicamente as instruções de sistema com base no Modo Escolhido!
        if mode == "coauthor":
            instruction_behavior = f"""
            Regra Suprema de Co-Autoria:
            - VOCÊ NÃO DEVE REESCREVER, ALTERAR OU RESUMIR O TEXTO ORIGINAL DO USUÁRIO. 
            - O texto original do usuário deve ser copiado INTEGRALMENTE no campo 'content_markdown'.
            - A sua única tarefa é atuar como Editor de Arte: aplique marcações em negrito (**) nas passagens mais marcantes e separe o texto original em seções lógicas inserindo cabeçalhos Markdown (##) para tornar a leitura mais fluida.
            """
        else: # ghostwriter
            instruction_behavior = f"""
            Regra Suprema de Ghostwriting:
            - Você deve reescrever e polir o relato caótico do usuário, transformando-o em uma crônica de viagem fluida e cativante em Markdown.
            - Mantenha a essência, as gírias de {persona.name} e o tom de voz especificado.
            - Organize o desenvolvimento dividindo o texto em seções lógicas usando cabeçalhos markdown (##).
            """

        system_instruction = f"""
        Você é o Gêmeo Digital de {persona.name}. Você é um cronista de viagem reflexivo, sincero e entusiasmado.
        
        Suas diretrizes de estilo de escrita:
        - Tom de voz: {persona.tone}
        - Estilo geral: {persona.writing_style}
        - Gírias recomendadas para usar naturalmente: {persona.slangs}
        - Termos estritamente PROIBIDOS: {persona.avoided_words}
        
        {instruction_behavior}
        
        Sua Missão:
        Gerar os metadados e o conteúdo do artigo baseado no relato original do usuário.
        
        Diretrizes de Estrutura do Artigo:
        1. Título: Deve ser impactante, poético e sem clichês de turismo (ex: não use 'Florença: A Cidade da Arte'). Crie algo que instigue a leitura de verdade.
        2. Subtítulo: Uma frase reflexiva que resuma o núcleo do aprendizado ou sentimento vivido.
        3. suggested_reading_time_minutes: Calcule de forma realista com base no tamanho final do texto (considerando aprox. 200 palavras por minuto).
        """

        user_prompt = f"Aqui está o meu relato de viagem bruto para processamento no modo [{mode.upper()}]:\n\n{raw_text}"
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.5, # Mantém a obediência às instruções bem rígida
                response_mime_type="application/json",
                response_schema=TripArticleOutputSchema,
            ),
        )
        
        try:
            output = TripArticleOutputSchema.model_validate_json(response.text)
            output.trip_id = trip_id
            output.generated_at = datetime.now(timezone.utc)
            return output
        except Exception as e:
            raise RuntimeError(f"Falha ao mapear Artigo no modo {mode}: {str(e)}. Resposta: {response.text}")