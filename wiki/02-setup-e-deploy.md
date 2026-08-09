# 02 - Setup e Deploy

## Configuração do Ambiente Local (Passo a Passo)

### 1. Pré-requisitos
*   **Docker** e **Docker Compose** instalados na máquina.
*   Chave de API válida da **OpenAI**.
*   Ambiente Python 3.11+ (se desejar rodar testes localmente).

### 2. Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto (use o `.env.example` como base). As variáveis obrigatórias são:

*   `OPENAI_API_KEY`: Chave da API da OpenAI.
*   `CHAINLIT_AUTH_SECRET`: Segredo aleatório para assinatura de tokens do Chainlit.
*   `DB_HOST`: Host do banco (ex: `postgres` ou `localhost`).
*   `DB_PORT`: Porta do banco (ex: `5432`).
*   `DB_NAME`: Nome do banco de dados.
*   `DB_USER`: Usuário do banco.
*   `DB_PASSWORD`: Senha do banco.
*   `APP_IMAGE` (Opcional): Nome da imagem Docker a ser construída.

### 3. Instalação e Execução
Como o projeto é 100% conteinerizado, basta executar:
```bash
docker compose up --build -d
```
O Docker iniciará o serviço de banco de dados e a API (que, por sua vez, usa o Supervisord para levantar o `api_server.py` e o `mcp_server.py`). O `alembic upgrade head` será rodado no pré-start via container de migrations para garantir o schema atualizado.

### 4. Acesso
*   Acesse o sistema em: `http://localhost:8080`

### 5. Fluxo de Deploy (Resumo)
1.  **CI/CD:** O repositório utiliza GitHub Actions (inferido) para CI.
2.  **Testes Automatizados:** Para rodar os testes de validação, execute:
    ```bash
    pytest --cov=. --cov-report=html
    ```
3.  **Containers:** Em produção, as imagens devem ser empurradas (push) para um registry de contêineres e inicializadas usando o mesmo arquivo `docker-compose.yml`, assegurando as variáveis seguras injetadas via secrets.
