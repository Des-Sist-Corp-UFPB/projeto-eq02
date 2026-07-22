# 04 - Inteligência e Modelos (IA)

## Orquestração do Agente (LangGraph)
O cérebro do assistente vive em `agent.py`. Utiliza-se um **StateGraph** que trafega o histórico de mensagens e o CPF ativo (`cpf_ativo`) do cliente.
*   O contexto longo de conversa é mantido pelo `MemorySaver` (Checkpointing interno).

## Prompting e Diretrizes (System Message)
O prompt do sistema é robusto e possui restrições explícitas:
1.  **Contextualização Diária**: O sistema sempre insere a data de hoje no prompt.
2.  **Roteiro**: Obrigatoriedade de iniciar o atendimento chamando a tool `obter_roteiro_atendimento`.
3.  **Proatividade**: O LLM deve notificar rompimento de metas se detectado durante um novo lançamento.
4.  **Guardrails e Escopo**: Restrição rígida a assuntos não financeiros.
5.  **Prompt Injection Check**: O uso da ferramenta `verificar_prompt_injection` é mandatório antes de aceitar comandos de modificação comportamental.

## Server-Sent Events (SSE) e Ferramentas (MCP)
As operações da IA não são executadas nativamente no agente. Ele usa um servidor assíncrono (FastMCP) para evitar gargalos bloqueantes:
*   **Namespaces registrados**: `clients`, `transactions`, `goals`, `memory`, `advisor`, `behavior`, `security`.
*   A comunicação ocorre via classe `MultiServerMCPClient` que injeta as definições no LLM (`bind_tools`).

## Pipelines Acoplados
*   **Whisper**: A extração de áudios `.webm`/`.wav` nativos é processada, convertida de PCM bruto para WAVE 16-bit Mono, e enviada ao OpenAI Whisper (`whisper-1`).
*   **TTS Automático**: Toda resposta em áudio gera o TTS da OpenAI com voz `nova`. Apenas gerado caso o input do usuário tenha sido um áudio, poupando custos de API.

> [!IMPORTANT]
> A API da OpenAI requer os bytes em formato Wav/Container válido. O `chat_app.py` realiza o resample de buffers do Chainlit `(24kHz PCM) -> WAV` em memória via `io.BytesIO`.
