# 🏦 FinancIA's - Assistente Financeiro Inteligente

Bem-vindo ao **FinancIA's**! Este é um projeto de agente conversacional autônomo (baseado em LangGraph) projetado para atuar como o seu assistente financeiro pessoal. Ele não é apenas um chat, é um agente que possui acesso a ferramentas (Tools) para consultar, criar e gerenciar o seu fluxo de caixa diretamente em um banco de dados relacional.

## 🌟 Principais Recursos
- **Agente Autônomo Consultivo (LangGraph):** Capaz de tomar decisões, consultar dados do usuário e atuar como um verdadeiro consultor financeiro usando a regra 50/30/20.
- **Onboarding Dinâmico e Inteligente:** Através de roteiros gerados no backend, o agente identifica se o usuário é novo (e pede a renda com educação em um bate-papo) ou se já é cliente (oferecendo ações diretas).
- **Ferramentas Avançadas (MCP):** O agente se conecta a um servidor MCP (Model Context Protocol) para rodar simulações de investimentos (juros compostos), analisar seu fluxo de caixa e atualizar sua renda e metas em tempo real.
- **Gravação de Áudio ao Vivo e Respostas em Voz (TTS):** Envie mensagens de voz diretamente pela interface! O backend transcreve o áudio via OpenAI Whisper e o Agente responde não apenas em texto, mas com áudio gerado dinamicamente (Text-to-Speech) para você ouvir a resposta.
- **Suporte a Compras Parceladas:** O sistema compreende e fatiar compras parceladas no cartão de crédito, diluindo o impacto do valor total apenas na proporção exata da parcela nos meses vigentes.
- **Login e Segurança:** Páginas de cadastro e login protegidas. O assistente só funciona se você for um usuário autenticado.
- **Integração com Supabase:** Banco de dados remoto robusto, pronto para o futuro uso do `pgvector`.
- **Interface Híbrida (Chainlit + HTML/JS):** Telas de Login fluidas desenvolvidas em Vanilla JS que redirecionam perfeitamente para o chat avançado no Chainlit.
- **Containerização Total:** Toda a aplicação e suas integrações rodam perfeitamente em um único ambiente Docker isolado.

## 🤖 O Que o Agente Sabe Fazer? (Funcionalidades)
Graças à integração com múltiplas ferramentas (Tools) via protocolo MCP, o Assistente Financeiro atua de forma autônoma nestas frentes:

1. **Gestão de Renda e Onboarding:**
   - Detecta novos usuários e conduz um bate-papo inicial amigável para descobrir e registrar a renda mensal.
   - Atualiza a renda a qualquer momento caso o usuário receba um aumento ou mude de emprego.

2. **Controle de Gastos e Despesas:**
   - **Registro Natural:** O usuário pode apenas dizer "Gastei 50 reais de ifood ontem" e o agente entende o valor, a data e a categoria (Alimentação), salvando no banco.
   - **Correção Inteligente e Exclusão:** Cometeu um erro ao registrar? Basta dizer "na verdade o lanche não foi 15 reais, foi 10" e o assistente identifica automaticamente qual gasto você está corrigindo e atualiza o valor no banco de dados. Você também pode pedir para o agente apagar uma transação duplicada.
   - **Compras Parceladas:** Registre compras divididas no cartão (ex: "Comprei uma TV de R$5000 em 10x"). O Agente deduzirá de forma fracionada o valor de cada parcela exclusivamente no mês correspondente do seu fluxo de caixa.
   - **Ciclo Mensal e Contas a Pagar:** O assistente diferencia automaticamente o que são *gastos efetivados* e o que são *contas pendentes*. Ele avisa quantos dias faltam para a conta vencer e projeta o saldo livre descontando os boletos a pagar.
   - **Comandos de Voz:** Sem vontade de digitar? Aperte o microfone na tela, fale seus gastos ou faça perguntas por áudio e veja o agente transcrever e executar a tarefa!
   - **Consultas e Relatórios:** O agente pesquisa no histórico e traz resumos como "Quanto gastei com lazer esse mês?".

3. **Orçamentos e Metas Mensais:**
   - O usuário pode definir limites (ex: "Não quero gastar mais de R$ 500 com transporte").
   - **Alerta Proativo:** Sempre que um novo gasto for registrado, o agente verifica sozinho se a meta foi ultrapassada e puxa a orelha do usuário com conselhos se necessário.

4. **Consultoria e Fluxo de Caixa (Regra 50/30/20):**
   - O agente não apenas anota, ele analisa! Ele compara os gastos dos últimos 30 dias com a renda atual.
   - Aplica a famosa regra 50% (Necessidades), 30% (Desejos) e 20% (Futuro), mostrando onde o usuário está errando no orçamento e calculando a taxa de queima mensal (*burn rate*).

5. **Consultoria Ativa de Investimentos:**
   - Se o usuário perguntar sobre o futuro, o agente roda um simulador matemático de juros compostos.
   - Responde dúvidas como: "Se eu investir R$ 300 por mês rendendo 10% ao ano, quanto terei em 5 anos?".
   - **Sugestão Pró-ativa (Gatilhos):** Sempre que a análise de fluxo de caixa mostrar que o usuário vai fechar o mês com o *Saldo Livre Projetado* positivo, o assistente ativa uma ferramenta dedicada para recomendar investimentos (ex: CDB de Liquidez Diária, Tesouro Selic, FIIs ou ETFs) baseados exatamente no valor que vai sobrar na conta.

6. **Memória Contínua:**
   - Salva informações chave sobre os objetivos do cliente na memória (ex: "Economizando para casar") e usa esse contexto no início de novas conversas para dar um toque extremamente pessoal ao atendimento.

## 🏗️ Arquitetura do Sistema
1. **Frontend HTML/JS (`static/`):** Telas rápidas e fluidas para gerenciar o acesso sem pedir dados excessivos logo de cara.
2. **Servidor API (`api_server.py`):** Feito em FastAPI, ele hospeda os arquivos HTML, valida o login com o banco de dados e emite um Cookie seguro.
3. **Chat Engine (`chat_app.py`):** Construído em Chainlit. Ele intercepta o Cookie de login, identifica o usuário via CPF e aciona o Agente, delegando a responsabilidade do roteiro inicial para o backend.
4. **Servidor de Ferramentas (`mcp_server.py`):** Implementa o protocolo MCP (*Model Context Protocol*) para expor de forma limpa, modular e segura todas as ferramentas de banco de dados, memória e matemática (simuladores).
5. **Cérebro (`agent.py`):** O Grafo de Estado (LangGraph) do agente, conectando o LLM (OpenAI) ao servidor de ferramentas usando adaptadores oficiais do MCP.
6. **Diagnóstico Embutido:** Uma rota especial (`/debug_db`) disponível na API para que desenvolvedores possam verificar rapidamente se as tabelas e dados falsos foram criados corretamente no PostgreSQL.

## 🚀 Como Executar o Projeto Localmente

A aplicação foi feita para ser **100% conteinerizada**, facilitando ao máximo o processo de execução.

### 1. Pré-requisitos
- Ter o [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado na sua máquina.
- Uma chave da API da **OpenAI** (`OPENAI_API_KEY`).
- Um projeto no **Supabase** configurado com as tabelas do projeto.

### 2. Configurando as Chaves
Na raiz do projeto, crie ou garanta que o seu arquivo `.env` contenha as seguintes variáveis com suas credenciais:
```env
SUPABASE_URL=sua_url_do_supabase
SUPABASE_SERVICE_KEY=sua_service_key_do_supabase
OPENAI_API_KEY=sua_chave_da_openai
CHAINLIT_AUTH_SECRET=uma-chave-aleatoria-bem-segura
```

### 3. Rodando com Docker
Abra o terminal na pasta raiz do projeto e execute:
```bash
docker-compose up --build -d
```

O Docker irá compilar a imagem única do projeto e iniciar o servidor.

### 4. Acessando a Aplicação
Acesse a interface no seu navegador através de:
👉 **[http://localhost:8000](http://localhost:8000)**
*(Se o localhost falhar devido a cache no Windows, tente [http://127.0.0.1:8000](http://127.0.0.1:8000))*

1. Faça seu Cadastro clicando em "Cadastre-se".
2. Faça o Login com seu E-mail e CPF.
3. O assistente de Chat carregará automaticamente, lhe chamando pelo nome e pronto para registrar seus gastos!