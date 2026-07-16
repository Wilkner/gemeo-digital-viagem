# Gêmeo Digital de Viagem

Este projeto implementa uma engine assíncrona baseada em Clean Architecture e FastAPI para receber relatos brutos de viagem (textos livres e metadados de imagens) e, por meio de inteligência artificial generativa adaptada a uma persona, convertê-los em diversos formatos de saída (ex: Stories do Instagram, artigos Markdown, Podcasts).

---

## 🛠️ Tecnologias e Stack Backend

- **Python 3.10+**
- **FastAPI** (Exposição da API REST)
- **Uvicorn** (Servidor ASGI assíncrono com Hot Reload)
- **Pydantic v2** (Validação rigorosa de contratos e schemas de dados)
- **Python-dotenv** (Gerenciamento de variáveis de ambiente)

---

## 📁 Estrutura do Projeto

A organização de pastas segue a separação por responsabilidades inspirada em Clean Architecture:

```text
gemeo-digital-viagem/
│
├── app/
│   ├── __init__.py
│   ├── main.py                 # Ponto de entrada da aplicação FastAPI
│   │
│   ├── api/                    # Camada de Exposição (HTTP/REST)
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── endpoints.py    # Rotas de ingestão e outputs (Stories)
│   │
│   ├── core/                   # Configurações globais e segurança
│   │   ├── __init__.py
│   │   └── config.py
│   │
│   ├── schemas/                # Contratos de Dados (Pydantic Models)
│   │   ├── __init__.py
│   │   └── trip.py
│   │
│   └── services/               # Lógica de Negócio e LLM Orchestration
│       ├── __init__.py
│       ├── persona.py          # Camada 1: Engine de Persona
│       └── agents.py           # Camada 3: Adaptadores de Formato (Stories/Markdown)
│
├── venv/                       # Ambiente virtual Python local (gerado pelo setup)
├── requirements.txt            # Dependências do ecossistema
└── README.md                   # Documentação do projeto
```

---

## 🚀 Setup e Execução do Servidor

Siga os passos abaixo para configurar o ambiente e rodar o servidor em modo de desenvolvimento local:

### 1. Criar o Ambiente Virtual (`venv`)
Caso ainda não o tenha criado:
```bash
python -m venv venv
```

### 2. Ativar o Ambiente Virtual
- **Windows (PowerShell)**:
  ```powershell
  .\venv\Scripts\activate
  ```
- **macOS / Linux**:
  ```bash
  source venv/bin/activate
  ```

### 3. Instalar as Dependências
```bash
pip install -r requirements.txt
```

### 4. Inicializar o Servidor (Uvicorn)
Com o ambiente ativado, execute o servidor em modo hot-reload:
```bash
uvicorn app.main:app --reload
```
O servidor estará rodando em: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 🔌 Endpoints Disponíveis (API V1)

- **Root check**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Documentação Interativa (Swagger/OpenAPI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Ingestão de Viagens (`POST`)**: `/api/v1/trips/ingest`
- **Output para Stories (`GET`)**: `/api/v1/trips/{trip_id}/output/stories`
