# 03 - Arquitetura de Dados

## Entidades Principais e Banco de Dados
O sistema utiliza PostgreSQL. A gerência do esquema relacional e das migrações é feita de ponta a ponta pelo **Alembic** (diretório `alembic/`).

### Tabelas Centrais (Inferidas)
*   **`clients`**: 
    *   `id`, `nome`, `cpf` (único, chave de identificação principal em todo o sistema), `email`, `password_hash`, `renda_total`.
*   **`audit_logs`**:
    *   Criada via migration (`006_audit_logs.py`).
    *   Registra ações de login, falhas e operações sensíveis (`action`, `user_cpf`, `details` JSON).
*   **(Tabelas de Transações, Categorias e Metas)**: Gerenciadas no DB e acessadas pelas ferramentas do MCP para calcular o fluxo de caixa, pendências e rate rates.

## Fluxo de Persistência e Processamento
*   **Pool de Conexões**: Controlado em `tools/db.py` via `psycopg2.pool.ThreadedConnectionPool`.
*   **Queries Diretas**: As inserções e buscas evitam a complexidade pesada de ORMs completos (como SQLAlchemy) nas ferramentas, utilizando queries cruas seguras (`execute_query`, `execute_insert`) mitigando injeções de SQL via tuplas seguras.
*   **Processamento Analítico**: A lógica pesada não mora nos endpoints da API, mas sim na pasta `tools/` (ex: `tools/advisor.py`), garantindo que tanto a API quanto a IA tenham a mesma regra de negócio lendo o banco.

> [!WARNING]
> Nunca modifique a estrutura das tabelas escrevendo comandos DDL manuais no banco. Todo alter de schema DEVE gerar uma nova migration via Alembic (`alembic revision --autogenerate`).
