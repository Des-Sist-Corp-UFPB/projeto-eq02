# 01 - Visão Geral do Projeto

## Propósito e Problema que Resolve
O **FinancIA's** é um Assistente Financeiro Inteligente projetado para atuar como um consultor pessoal do usuário. Ele resolve o problema da complexidade na gestão financeira ao unir a interação natural de uma Inteligência Artificial conversacional com a precisão analítica de um Dashboard Financeiro (nível executivo).
Através de uma interface híbrida, a IA controla dinamicamente o que o usuário vê: exibe gráficos durante conversas sobre fluxo de caixa e oculta o painel analítico para focar no texto durante conversões mais complexas sobre investimentos e conselhos.

## Stack Tecnológica

### Backend e Infraestrutura
*   **Linguagem:** Python 3.11+
*   **Frameworks Web:** FastAPI (API principal) e Chainlit (Chat Engine)
*   **Banco de Dados:** PostgreSQL (gerenciado via Docker)
*   **Migrations:** Alembic
*   **Orquestração de Processos:** Supervisord (Garante que a API e o servidor MCP subam no mesmo container de forma segura)
*   **Containerização:** Docker e Docker Compose

### Inteligência Artificial e LLM
*   **Orquestração de Agente:** LangGraph (StateGraph) e LangChain
*   **Protocolo de Ferramentas:** FastMCP (Model Context Protocol), conectando a IA de forma segura aos dados
*   **LLMs e Modelos:**
    *   **Cérebro:** OpenAI `gpt-4o-mini`
    *   **Transcrição de Áudio:** OpenAI Whisper (`whisper-1`)
    *   **Geração de Voz (TTS):** OpenAI TTS (`tts-1`)

### Frontend
*   **Interface:** HTML5, CSS3 nativo (Glassmorphism, Neon UI, Tema Escuro)
*   **Lógica:** JavaScript (Vanilla) com Chart.js para renderização dos gráficos interativos
*   **Comunicação em Tempo Real:** WebSockets e Server-Sent Events (SSE)
