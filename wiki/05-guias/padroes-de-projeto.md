# 05 - Guias: Padrões de Projeto

## Arquitetura de Pastas e Convenções
*   `/tools`: Módulos de regras de negócios, abstração de banco de dados e MCP server functions.
*   `/static`: Exclusivo para HTML/CSS/JS e assets visuais (Dashboard frontend puro).
*   `/alembic`: Exclusivo para as versões/migrations do banco.
*   `/tests`: Padrão Pytest. Testes de unidade com injeção/mocks de DB para manter alta velocidade.

## Convenções de Código (Python)
1.  **Funções e Variáveis:** `snake_case`.
2.  **Classes:** `CamelCase`.
3.  **Importações:** Evitar dependências circulares, isolando a lógica financeira dentro de `tools/` de forma agnóstica de frameworks web (ou seja, `tools/` não deve importar dependências do FastAPI ou Chainlit).

## Controle de Qualidade (Linting e Testes)
*   **Cobertura**: A meta mínima do projeto é manter a cobertura acima de 90% (Atualmente em 93%). Para aferir o relatório, visualize em `htmlcov/` após rodar o comando:
    ```bash
    pytest --cov=. --cov-report=html
    ```
*   **Tratamento de Exceções**: A API utiliza os decoradores de `app.exception_handler` globais para padronizar o retorno de Erros Críticos (500) e Validações (422), retornando JSON limpo e seguro (sem stacktraces).

## Pontos de Atenção / A Revisar
*   **Logs Consolidados**: Atualmente há vários `print()` espalhados para debugar Chainlit. O ideal no longo prazo é usar o módulo nativo `logging` padrão do Python, configurado na raiz.
