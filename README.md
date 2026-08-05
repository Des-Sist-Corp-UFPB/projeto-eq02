# 🏦 FinancIA's - Assistente Financeiro Inteligente

Bem-vindo ao **FinancIA's**! Este é um projeto de agente conversacional autônomo (baseado em LangGraph) projetado para atuar como o seu assistente financeiro pessoal. Ele não é apenas um chat, é um ecossistema híbrido que une a inteligência de um consultor IA com a precisão visual de um Dashboard financeiro de nível executivo.

## 🌟 Principais Recursos
- **Interface Híbrida Inteligente:** A tela divide-se dinamicamente entre o Chat e um **Dashboard de Controle**. A IA controla a visibilidade da tela: ao falar de fluxo de caixa, os gráficos aparecem; ao focar em investimentos e conversas complexas, o painel se esconde para focar no chat. Você também pode redimensionar as telas arrastando a divisória central!
- **Dashboard Neon (Glassmorphism):** Um painel analítico lindíssimo construído nativamente em JS (Chart.js) com tema escuro, efeitos de vidro (blur), sombras e gráficos neon vibrantes. Exibe histórico de evolução do saldo, composição do fluxo de caixa e divisão de gastos por categoria em tempo real.
- **Agente Autônomo Consultivo (LangGraph):** Capaz de tomar decisões, consultar dados e atuar como consultor financeiro aplicando a regra 50/30/20.
- **Onboarding Dinâmico e Inteligente:** O agente identifica se o usuário é novo (pedindo a renda educadamente) ou se já é cliente (oferecendo ações diretas).
- **Streaming de Digitação:** A IA agora responde com um efeito de digitação em tempo real super rápido, trazendo uma experiência de conversa muito natural e imersiva.
- **Ferramentas Avançadas (MCP):** O agente se conecta a um servidor MCP (Model Context Protocol) para gerenciar o banco de dados e simular investimentos.
- **Gravação e Transcrição (Whisper) + Respostas em Voz (TTS):** Envie áudios! O backend transcreve o áudio via OpenAI Whisper e o Agente responde não apenas em texto, mas com áudio gerado dinamicamente para você ouvir.
- **Login Seguro e Sessão Global:** Toda a sua conversa e o dashboard estão isolados e atrelados ao seu CPF em um banco de dados **PostgreSQL**.

## 🤖 O Que o Agente Sabe Fazer?
1. **Gestão de Renda e Gastos Naturais:** Diga "Gastei 50 no ifood" e ele extrai valor, data e categoria.
2. **Correção e Compras Parceladas:** Corrige lançamentos por voz/texto ("na verdade foi 10 reais") e compreende parcelamentos, diluindo o valor nos meses corretos.
3. **Contas a Pagar:** Diferencia gastos efetivados de faturas pendentes, informando o que falta pagar.
4. **Metas Proativas:** Checa se a sua meta mensal de gastos de uma categoria foi rompida e te avisa no ato.
5. **Consultoria 50/30/20:** Analisa a sua saúde financeira, calcula o seu "burn rate" e diz onde você precisa economizar.
6. **Investimentos Livres de Gráficos Poluídos:** Ao invés de misturar telas, a IA foca no texto e em explicar as opções disponíveis e projeções numéricas, mantendo o ambiente limpo.

## 🏗️ Arquitetura do Sistema (Pronto para Produção)
O projeto foi refatorado para atender altos padrões de engenharia de software e microserviços:

1. **Frontend HTML/JS + CSS:** Arquivos nativos leves (`hibrido.html`, `dashboard.js`) que renderizam os painéis, gerenciam o *drag-to-resize* e a reatividade do Dashboard com Chart.js.
2. **Process Manager (Supervisor):** O container principal utiliza o `supervisord` para orquestrar a inicialização segura, garantindo que as migrações do banco (Alembic) rodem antes dos servidores web.
3. **Servidor API (`api_server.py`):** Desenvolvido em FastAPI rodando na porta **8080**. Hospeda os arquivos estáticos, rotas de autenticação (Login/Registro com hash bcrypt), tratamento global de exceções, e entrega os JSONs financeiros que abastecem o Dashboard.
4. **Chat Engine (`chat_app.py`):** Construído em Chainlit, processa o áudio, lida com a interceptação das *Tools* para controlar o UI do dashboard, e gera as mensagens na tela usando *Streaming*.
5. **Servidor de Ferramentas (`mcp_server.py`):** Roda como um processo independente na porta **8000** via transporte **SSE (Server-Sent Events)**. Expõe as funções matemáticas e de banco de dados no padrão Model Context Protocol.
6. **Cérebro (`agent.py`):** O Grafo de Estado (LangGraph) do agente, conectando o LLM (OpenAI) ao MCP Server via chamadas HTTP (SSE).
7. **Banco de Dados (PostgreSQL + Alembic):** Container nativo de PostgreSQL gerenciado pelo docker-compose. O controle de versão do schema é feito via Alembic.
8. **Bateria de Testes (Pytest):** O projeto conta com testes automatizados focados em API e Utils, utilizando injeção de dependência e `mocking` para garantir a qualidade sem poluir o banco real.

## Log de Auditoria

O sistema possui um módulo persistente de auditoria para registrar ações de
segurança e alterações relevantes nos dados financeiros. O objetivo é permitir
rastrear **quem realizou a ação, qual operação ocorreu, quando ocorreu e quais
dados de contexto foram afetados**.

### Eventos auditados

| Evento (`action`) | Operação registrada | Informações salvas em `details` |
|---|---|---|
| `LOGIN_SUCCESS` | Login concluído | Identificação do usuário pelo CPF |
| `LOGIN_FAILED` | Tentativa de login inválida | Motivo: usuário inexistente ou senha inválida |
| `REGISTER` | Cadastro pela API | Nome e e-mail cadastrados |
| `CLIENT_REGISTERED_VIA_MCP` | Cadastro realizado por ferramenta MCP | ID do cliente e e-mail |
| `TRANSACTION_CREATED` | Criação de gasto ou conta a pagar | ID, valor, categoria, data, status, parcelas e recorrência |
| `TRANSACTION_UPDATED` | Alteração ou pagamento de uma transação | ID, campos alterados, valor, categoria e status resultantes |
| `TRANSACTION_DELETED` | Exclusão de transação | ID do registro excluído |
| `GOAL_CREATED` | Criação de meta mensal | ID, categoria, limite e competência da meta |
| `INCOME_UPDATED` | Alteração da renda mensal | Valor anterior e novo valor |
| `MEMORY_CREATED` | Gravação de memória do assistente | ID da memória, sem copiar seu conteúdo privado para o log |

As consultas de leitura não são gravadas, evitando ruído e crescimento
desnecessário da tabela. Senhas, hashes, tokens e o texto das memórias **nunca
são armazenados no log de auditoria**.

### Armazenamento

Os eventos ficam na tabela PostgreSQL `audit_logs`, criada pela migration
`alembic/versions/006_audit_logs.py`:

| Campo | Tipo | Finalidade |
|---|---|---|
| `id` | UUID | Identificador único do evento |
| `action` | VARCHAR(100) | Nome padronizado da ação |
| `user_cpf` | VARCHAR(11) | Usuário associado ao evento |
| `details` | TEXT contendo JSON | Metadados específicos da operação |
| `created_at` | TIMESTAMP WITH TIME ZONE | Data e hora UTC geradas pelo banco |

### Implementação e fluxo

O serviço central `tools/audit.py` expõe `log_action(action, user_cpf,
details)`. Ele serializa os detalhes em JSON e executa um `INSERT` parametrizado
por meio de `tools/db.py`. Cada ação de escrita chama esse serviço somente após
a operação principal retornar sucesso:

```text
Usuário/API/Agente
        ↓
operação de negócio concluída
        ↓
log_action(ação, CPF, detalhes seguros)
        ↓
INSERT parametrizado em audit_logs
```

Arquivos participantes:

- `tools/audit.py`: serviço central de auditoria e serialização segura do JSON.
- `tools/db.py`: pool de conexões e execução parametrizada no PostgreSQL.
- `api_server.py`: auditoria de login, falha de login e cadastro pela API.
- `tools/transactions.py`: criação, edição e exclusão de transações.
- `tools/goals.py`: criação de metas financeiras.
- `tools/clients.py`: cadastro via MCP e alteração de renda.
- `tools/memory.py`: registro da criação de memória sem expor seu conteúdo.
- `alembic/versions/006_audit_logs.py`: criação e reversão da tabela.
- `tests/test_audit.py`: testes automatizados do serviço de auditoria.

Para verificar os eventos diretamente no ambiente local:

```sql
SELECT id, action, user_cpf, details, created_at
FROM audit_logs
ORDER BY created_at DESC;
```

## Integração com Serviço Externo
- **Qual é o serviço externo:** OpenAI.
- **Para que é usado:** Utilizado como o cérebro da inteligência artificial do assistente (modelo `gpt-4o-mini` via LangGraph), para transcrição de áudio via Whisper e geração de áudio (Text-to-Speech) de forma dinâmica para as respostas do assistente.
- **Quais arquivos participam:**
  - `chat_app.py` (gerenciamento das chamadas da API da OpenAI para TTS e Transcrição/Whisper)
  - `agent.py` (configuração e uso do LLM no LangGraph)
- **Como é configurado:** Através da variável de ambiente `OPENAI_API_KEY` injetada no container via arquivo `.env`.

## 🚀 Como Executar o Projeto Localmente

A aplicação é **100% conteinerizada**, pronta para produção. O banco de dados já sobe junto com o projeto.

### 1. Pré-requisitos
- Docker Desktop instalado.
- Chave da API da **OpenAI** (`OPENAI_API_KEY`).

### 2. Configurando as Chaves
Na raiz do projeto, crie o arquivo `.env`:
```env
OPENAI_API_KEY=sua_chave_da_openai
CHAINLIT_AUTH_SECRET=uma-chave-aleatoria-bem-segura
```

### 3. Rodando com Docker
Basta subir os containers. O banco de dados (PostgreSQL) será criado e o Alembic cuidará de construir todas as tabelas automaticamente.
```bash
docker compose up --build -d
```

*(Nota: o container aguardará pacientemente as migrações do banco terminarem antes de liberar o healthcheck).*

### 4. Testes Automatizados e Cobertura (93%)
Para rodar a bateria de testes de forma limpa e rápida na sua máquina (é recomendável usar um ambiente virtual local):
```bash
pytest --cov=. --cov-report=html
```
O percentual atual de cobertura automatizada de testes para este repositório alcançou **93%**, o relatório completo foi gerado e pode ser consultado na pasta `cobertura/`.

### 5. Acessando a Aplicação
Acesse no seu navegador através de:
👉 **[http://localhost:8080](http://localhost:8080)**

1. Faça seu Cadastro.
2. Faça o Login.
3. Você será redirecionado para a plataforma híbrida, com seu Chat e seu Dashboard trabalhando juntos!
