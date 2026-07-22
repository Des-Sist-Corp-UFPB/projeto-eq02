# 03 - Arquitetura do Sistema

## Módulos e Comunicação
A arquitetura é projetada como um conjunto de serviços internos coordenados.

1.  **Frontend (`static/`)**: Composto por arquivos HTML/JS puros. Possui interface de Login e a interface Híbrida (`hibrido.html`). Interage via HTTP Rest e WebSockets.
2.  **API Server (`api_server.py`)**: Roda na porta 8080.
    *   Exibe os estáticos e gerencia a autenticação JWT e cookies de sessão (`auth_cpf`).
    *   Monta a rota `/chat` repassando para o App do Chainlit.
    *   Expõe o endpoint `/api/dashboard_data` para alimentar os gráficos.
3.  **Chat Engine (`chat_app.py`)**: Baseado em Chainlit. Processa áudio (Whisper), intercepta o fluxo de respostas (Streaming) e controla a UI (mostrando/escondendo o painel usando estado).
4.  **Cérebro (LangGraph em `agent.py`)**: Coordena as mensagens e conecta o LLM (`gpt-4o-mini`) com as ferramentas de banco de dados e finanças.
5.  **MCP Server (`mcp_server.py`)**: Roda em background (Porta 8000). Expõe as ferramentas financeiras usando SSE (Server-Sent Events) no padrão Model Context Protocol para o `agent.py`.

## Diagrama da Arquitetura
```mermaid
graph TD
    User([Usuário]) --> |Browser (HTTP 8080)| API[FastAPI Server]
    User --> |Browser (WS)| Chat[Chainlit Chat Engine]
    
    API --> |Cookies & JWT| Chat
    API --> |/api/dashboard_data| DB[(PostgreSQL)]
    
    Chat --> |Whisper / TTS| OpenAI[OpenAI API]
    Chat --> |Astream / Invoca| Agent[LangGraph Agent]
    
    Agent --> |LLM Inference| OpenAI
    Agent --> |SSE Request (Port 8000)| MCP[FastMCP Server]
    
    MCP --> |Queries & Regras| DB
```

> [!NOTE]
> O estado visual do Dashboard é mantido no arquivo `state.py` (dicionário global em memória) que a API lê para repassar via `/api/dashboard_data` e o `chat_app.py` atualiza dependendo do contexto da conversa.
