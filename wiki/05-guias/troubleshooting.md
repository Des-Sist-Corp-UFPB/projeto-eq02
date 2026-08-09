# 05 - Guias: Troubleshooting

## 1. Uvicorn "Unsupported upgrade request" Error
*   **Sintoma**: Logs massivos no console da API com a mensagem "Unsupported upgrade request".
*   **Causa**: Interferência de proxies ou WebSockets órfãos sendo disparados pelo Chainlit para o FastAPI na porta 8080.
*   **Solução Atual**: Já implementada no projeto através da injeção de uma classe `FilterUpgrade` que herda de `logging.Filter` no `api_server.py`.

## 2. Chainlit Travando após Login (Loop de Sessão)
*   **Sintoma**: O chat acusa "Sessão inválida" ou fica congelado mesmo após login válido.
*   **Causa**: O Chainlit injeta cookies `HttpOnly` pesados chamados `access_token` e `session_id` que podem estragar as chamadas customizadas.
*   **Solução Atual**: O backend no `api_server.py` chama `.delete_cookie()` nestas rotas, repassando o CPF por `auth_cpf` capturado por `header_auth_callback` no `chat_app.py`.

## 3. Banco de Dados Não Inicializado
*   **Sintoma**: API trava logo no início alegando tabela não encontrada ou conexão falhou (`FATAL: password authentication failed`).
*   **Solução**: 
    1.  Verifique no seu `.env` as variáveis `DB_USER` e `DB_PASSWORD`.
    2.  Verifique se o container `migrations` obteve sucesso na execução (`docker logs <id_do_container_migrations>`). O container principal de API no Docker-Compose tem `depends_on: migrations: condition: service_completed_successfully`.

## 4. Agente Alucina ao Criar Gráficos no Chat
*   **Sintoma**: A IA começa a gerar tabelas em Markdown e gráficos poluindo o texto do Chat ao invés de atualizar o Dashboard visual.
*   **Solução**: Foi injetado o Guardrail no sistema, e também no final de certas mensagens em `chat_app.py`, proibindo a geração de lixo visual. Caso reocorra, verificar se a instrução do prompt em `agent.py` está sendo obedecida.
