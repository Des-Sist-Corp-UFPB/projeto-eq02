# 🏦 FinancIA's - Assistente Financeiro Inteligente

Bem-vindo ao **FinancIA's**! Este é um assistente financeiro conversacional baseado em LangGraph, MCP e PostgreSQL. O projeto combina atendimento por inteligência artificial, persistência de dados, pesquisa atualizada de investimentos e um dashboard executivo para transformar conversas em informações financeiras rastreáveis e visuais.

## 🌟 Principais Recursos
- **Interface Híbrida Inteligente:** A tela divide-se dinamicamente entre o Chat e um **Dashboard de Controle**. A IA controla a visibilidade da tela: ao falar de fluxo de caixa, os gráficos aparecem; ao focar em investimentos e conversas complexas, o painel se esconde para focar no chat. Você também pode redimensionar as telas arrastando a divisória central!
- **Dashboard Financeiro Responsivo:** Painel construído em JavaScript e Chart.js com renda, gastos realizados, contas pendentes, saldo projetado, renda comprometida, composição do caixa e gastos por categoria. O saldo e o percentual comprometido consideram também as pendências do mês.
- **Agente Autônomo Consultivo (LangGraph):** Capaz de tomar decisões, consultar dados e atuar como consultor financeiro aplicando a regra 50/30/20.
- **Onboarding Dinâmico e Inteligente:** O agente identifica se o usuário é novo (pedindo a renda educadamente) ou se já é cliente (oferecendo ações diretas).
- **Streaming de Digitação:** A IA agora responde com um efeito de digitação em tempo real super rápido, trazendo uma experiência de conversa muito natural e imersiva.
- **Ferramentas Avançadas (MCP):** O agente se conecta a um servidor Model Context Protocol para gerenciar clientes, transações, metas, memória, segurança, fluxo de caixa, pesquisa e simulação de investimentos.
- **Pesquisa Atualizada de Investimentos:** Um RAG leve combina o guia versionado na `wiki` com busca web em fontes institucionais. A resposta apresenta cinco alternativas, limita as referências exibidas a dez fontes e gera um gráfico comparativo para as taxas confirmadas.
- **Memória Persistente de Investimentos:** Quando o usuário informa qual investimento pretende fazer, a escolha, o valor e a data podem ser armazenados no PostgreSQL e recuperados em conversas futuras.
- **Auditoria e Observabilidade:** Escritas relevantes são auditadas no banco. OpenTelemetry envia traces, métricas e logs, enquanto o Umami acompanha a utilização das páginas.
- **Health Check Completo:** A rota `/ping` valida o serviço e executa `SELECT 1` no PostgreSQL; o Docker utiliza essa rota para determinar a saúde da aplicação.
- **Gravação e Transcrição (Whisper) + Respostas em Voz (TTS):** Envie áudios! O backend transcreve o áudio via OpenAI Whisper e o Agente responde não apenas em texto, mas com áudio gerado dinamicamente para você ouvir.
- **Login Seguro e Sessão Global:** Toda a sua conversa e o dashboard estão isolados e atrelados ao seu CPF em um banco de dados **PostgreSQL**.

## 🤖 O Que o Agente Sabe Fazer?
1. **Gestão de Renda e Gastos Naturais:** Diga "Gastei 50 no ifood" e ele extrai valor, data e categoria.
2. **Correção e Compras Parceladas:** Corrige lançamentos por voz/texto ("na verdade foi 10 reais") e compreende parcelamentos, diluindo o valor nos meses corretos.
3. **Contas a Pagar:** Diferencia gastos efetivados de faturas pendentes, informando o que falta pagar.
4. **Metas Proativas:** Checa se a sua meta mensal de gastos de uma categoria foi rompida e te avisa no ato.
5. **Consultoria 50/30/20:** Analisa a sua saúde financeira, calcula o seu "burn rate" e diz onde você precisa economizar.
6. **Pesquisa e Comparação de Investimentos:** Consulta fontes institucionais, apresenta alternativas atuais e exibe em um gráfico a evolução de um aporte inicial único, sem repetir a projeção de cada mês no texto.
7. **Categorização pelo Contexto:** Cada item é registrado separadamente e classificado pela finalidade real em Necessidades, Desejos ou Futuro, evitando categorias genéricas quando há contexto suficiente.
8. **Memória de Escolhas:** Se o usuário disser apenas que fará um investimento, o agente pergunta qual será. Após a resposta, salva a escolha e consegue recuperá-la posteriormente.
9. **Segurança do Agente:** Possui verificação de prompt injection, guardrails de escopo e uso obrigatório de ferramentas para dados e cálculos financeiros.

## 🏗️ Arquitetura do Sistema (Pronto para Produção)
O projeto foi refatorado para atender altos padrões de engenharia de software e microserviços:

1. **Frontend HTML/JS + CSS:** As versões atuais ficam em `static/acesso-v2.html`, `static/cadastro-v2.html`, `static/hibrido-v5.html`, `static/dashboard-v5.js`, `static/dashboard-v5.css` e `static/workspace-v5.css`. A interface controla o painel híbrido, o redimensionamento e os gráficos com Chart.js.
2. **Process Manager (Supervisor):** O container da API utiliza `supervisord` para manter o servidor MCP e o Uvicorn em execução, ambos instrumentados automaticamente pelo OpenTelemetry.
3. **Migrações Isoladas:** O serviço `migrations` do Docker Compose executa `alembic upgrade head` e precisa terminar com sucesso antes da inicialização da API.
4. **Servidor API (`api_server.py`):** FastAPI na porta **8080**, responsável pelos arquivos estáticos, autenticação com bcrypt/JWT, cookies de sessão, dashboard, tratamento de exceções, WebSocket, health checks e OpenAPI.
5. **Chat Engine (`chat_app.py`):** Chainlit responsável por áudio, streaming, indicador de pesquisa, interceptação das ferramentas, controle do dashboard, gráfico Plotly de investimentos e exibição compacta das fontes.
6. **Servidor de Ferramentas (`mcp_server.py`):** Processo independente via transporte **SSE**, expondo as ferramentas de negócio no padrão MCP.
7. **Cérebro (`agent.py`):** Grafo de estado LangGraph que conecta o modelo da OpenAI ao MCP, preserva o contexto da conversa e aplica as diretrizes financeiras e de segurança.
8. **Banco de Dados (PostgreSQL + Alembic):** Armazena clientes, transações, metas, memórias e auditoria. O schema é versionado pelas migrations em `alembic/versions`.
9. **Pesquisa de Investimentos (`tools/investment_research.py`):** Carrega `wiki/04-regras-de-negocio/guia-investimentos.md`, consulta fontes atuais e devolve data, relatório e referências utilizadas.
10. **Bateria de Testes (Pytest):** Testes de API, auditoria, segurança, ferramentas, fluxo financeiro, pesquisa e memória utilizam mocks para evitar dependência do banco e de serviços externos.

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
| `INVESTMENT_CHOICE_SAVED` | Registro da escolha de investimento | ID da memória, nome do investimento, valor e data informada |

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
- `tools/memory.py`: criação de memórias, persistência e recuperação do histórico de escolhas de investimento.
- `alembic/versions/006_audit_logs.py`: criação e reversão da tabela.
- `tests/test_audit.py`: testes automatizados do serviço de auditoria.

Para verificar os eventos diretamente no ambiente local:

```sql
SELECT id, action, user_cpf, details, created_at
FROM audit_logs
ORDER BY created_at DESC;
```

## Integração com Serviço Externo

### OpenAI

- **Para que é usado:** cérebro do assistente (`gpt-4o-mini` via LangGraph), pesquisa web atualizada, transcrição de áudio com Whisper e geração de voz com Text-to-Speech.
- **Arquivos participantes:** `agent.py`, `chat_app.py` e `tools/investment_research.py`.
- **Configuração:** variável de ambiente `OPENAI_API_KEY`, injetada pelo arquivo `.env` sem expor a chave no repositório.

### OpenTelemetry

- **Para que é usado:** coleta de traces, métricas e logs correlacionados da API, do servidor MCP e das operações financeiras.
- **Instrumentação:** os processos são iniciados com `opentelemetry-instrument` pelo Supervisor.
- **Configuração:** `OTEL_SERVICE_NAME`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_EXPORTER_OTLP_PROTOCOL`, `OTEL_EXPORTER_OTLP_HEADERS` e `OTEL_AUTH_TOKEN`.
- **Demonstração de erros:** a rota `/bug` gera uma falha controlada para validar a coleta de logs.

### Umami Analytics

- **Para que é usado:** coleta de visualizações e métricas de navegação da aplicação no painel central da disciplina.
- **Servidor:** `https://umami.dsc.rodrigor.com`.
- **Website ID da equipe:** `256f21b6-a00f-4b43-9bd0-457c56e9ec9e`.
- **Implementação:** script oficial do Umami carregado com `defer` antes do fechamento de `</head>`.
- **Páginas instrumentadas:** `static/acesso-v2.html`, `static/cadastro-v2.html`, `static/hibrido-v5.html` e `static/dashboard-only-v5.html`.
- **Segurança:** as credenciais de acesso ao painel não são armazenadas no código; somente o identificador público do website é enviado pelo frontend.

## 🚀 Como Executar o Projeto Localmente

A aplicação é **100% conteinerizada**, pronta para produção. O banco de dados já sobe junto com o projeto.

### 1. Pré-requisitos
- Docker Desktop instalado.
- Chave da API da **OpenAI** (`OPENAI_API_KEY`).

### 2. Configurando as Chaves
Na raiz do projeto, crie o arquivo `.env`:
```env
OPENAI_API_KEY=sua_chave_da_openai
OPENAI_WEB_SEARCH_MODEL=gpt-5.6
CHAINLIT_AUTH_SECRET=uma-chave-aleatoria-bem-segura
OTEL_AUTH_TOKEN=token_fornecido_para_telemetria
```

`OPENAI_WEB_SEARCH_MODEL` é opcional e define o modelo usado apenas na pesquisa
financeira atualizada. Quando não informada, a aplicação usa `gpt-5.6`.

### Pesquisa atualizada de investimentos

Perguntas sobre opções, taxas ou cenário atual acionam a ferramenta MCP
`pesquisar_investimentos_atualizados`. Ela lê o guia-base da `wiki`, consulta a
web no momento da pergunta e restringe a busca a fontes institucionais, como
Banco Central, Tesouro Direto, CVM, B3, FGC, ANBIMA e portais do Governo. A
pesquisa solicita cinco alternativas, prioriza as referências efetivamente
citadas e limita a exibição a dez fontes. A primeira fica visível e as demais
podem ser abertas pelo indicador `+N`.

As taxas anuais confirmadas são enviadas ao simulador determinístico. O aporte é
tratado como aplicação inicial única, salvo quando o usuário pedir explicitamente
aportes recorrentes. Os resultados são educacionais e não representam promessa
de rentabilidade ou recomendação individual.

### 3. Rodando com Docker
Basta subir os containers. O PostgreSQL será criado, o serviço de migrações executará o Alembic e somente depois a API será iniciada.
```bash
docker compose up --build -d
```

O health check do container chama `GET /ping`, que verifica a API e a conexão com o PostgreSQL. Em caso de falha no `SELECT 1`, a rota responde com status HTTP 500.

### 4. Testes Automatizados e Cobertura (93%)
Para rodar a bateria de testes de forma limpa e rápida na sua máquina (é recomendável usar um ambiente virtual local):
```bash
pytest --cov=. --cov-report=html
```
O relatório de cobertura versionado alcançou **93%** no momento em que foi gerado e pode ser consultado na pasta `cobertura/`. Como novas funcionalidades foram adicionadas posteriormente, execute o comando acima para obter o percentual referente ao código atual.

### 5. Acessando a Aplicação
Acesse no seu navegador através de:
👉 **[http://localhost:8080](http://localhost:8080)**

1. Faça seu Cadastro.
2. Faça o Login.
3. Você será redirecionado para a plataforma híbrida, com seu Chat e seu Dashboard trabalhando juntos!

## 🎥 Vídeo de Apresentação

Assista à demonstração do projeto no YouTube:

👉 **[FinancIA's — Apresentação e demonstração](https://youtu.be/K58ObQatSL8?is=h3p4oy79_PnhwaAG)**
