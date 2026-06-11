# 🗺️ Roadmap e Próximos Passos (FinancIA's)

Este documento descreve as próximas grandes funcionalidades e evoluções planejadas para o projeto, visando torná-lo um consultor financeiro ainda mais completo e pronto para produção.

## 1. Módulo de RAG para Investimentos (Retrieval-Augmented Generation)
**Objetivo:** Transformar o agente em um especialista avançado em investimentos.
- **Integração de Conhecimento:** O agente será capaz de ler e extrair dados de sites de finanças, relatórios de mercado e PDFs (ex: carteiras recomendadas, análises de fundos).
- **Respostas Embasadas:** Em vez de depender apenas do conhecimento pré-treinado do LLM, o agente buscará o contexto mais atualizado em uma base de dados vetorial (utilizando o `pgvector` já previsto no Supabase) antes de responder dúvidas sobre onde investir.

# Plano de Implementação: Módulo RAG para Investimentos (Via pgvector)

> ⚠️ **STATUS: AGUARDANDO PROFESSOR**
> Este plano está temporariamente em espera (Hold).
> Dependemos que o professor instale a extensão `pgvector` no servidor PostgreSQL acadêmico (e rode `CREATE EXTENSION vector;`) para prosseguirmos com a implementação desta arquitetura.

---

## Objetivo
Transformar o FinancIA's em um especialista de investimentos embasado em dados reais, utilizando a técnica de RAG (Retrieval-Augmented Generation) com PostgreSQL e `pgvector`. Isso permitirá que o agente busque informações em uma base de dados vetorial antes de responder a dúvidas complexas, reduzindo alucinações.

## Próximos Passos (A serem executados após liberação do banco)

### 1. Banco de Dados (`sql/`)
- Descomentar a linha `CREATE EXTENSION IF NOT EXISTS vector;` no arquivo `01_init_schema.sql` (se for rodar localmente depois)
- Criar a tabela `investment_knowledge` para armazenar os blocos de texto e o vetor gerado pela OpenAI:
```sql
CREATE TABLE IF NOT EXISTS investment_knowledge (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);
```

### 2. Dependências
- Adicionar `pgvector` ao `requirements.txt` para manipular dados vetoriais com a biblioteca `psycopg2`.

### 3. Script de Ingestão de Dados
- Criar a pasta `knowledge_base/` na raiz do projeto para guardarmos arquivos `.txt` (ex: `tesouro_direto.txt`).
- Criar um script `scripts/ingest_knowledge.py` que:
  1. Lê os arquivos `.txt` da pasta.
  2. Gera embeddings chamando a API da OpenAI (`text-embedding-3-small`).
  3. Insere o texto e o vetor na tabela `investment_knowledge`.

### 4. Servidor MCP (Ferramentas de Busca)
- Criar o arquivo `tools/rag/mcp.py` contendo a ferramenta: `pesquisar_conhecimento_investimentos(query: str)`.
- A ferramenta converterá a pergunta em vetor e usará o operador `<=>` (similaridade do cosseno) do pgvector para achar os textos mais relevantes.
- Montar a ferramenta no `mcp_server.py`.

### 5. Cérebro do Agente (`agent.py`)
- Atualizar o `sys_msg` (Prompt de Sistema) para forçar o uso da ferramenta: *"Sempre que o usuário fizer perguntas complexas sobre investimentos, utilize a ferramenta `pesquisar_conhecimento_investimentos` ANTES de responder para embasar suas dicas em dados reais."*

---

*(Este documento servirá de guia para retomarmos o trabalho assim que o servidor de banco de dados estiver pronto).*


## 2. Histórico de Saldo Mensal Automatizado no Banco
**Objetivo:** Substituir a simulação matemática do saldo no painel por dados reais persistidos e organizar a virada de mês.
- **Rotina de Fechamento (Cron Job):** Criar um processo no backend que execute no último dia de cada mês (ex: dia 30/31).
- **Snapshot do Saldo:** O sistema calculará o "Saldo Livre" restante daquele mês específico e salvará em uma nova tabela de histórico (`historico_saldo_mensal`).
- **Virada de Mês (Reset):** Após salvar o saldo, o sistema irá "limpar" (resetar/arquivar) as transações do mês que acabou, **mantendo ativas apenas as contas e rendas marcadas como recorrentes**.
- **Precisão Financeira:** Com isso, o gráfico de linhas do dashboard puxará a evolução 100% real de como o patrimônio líquido do usuário se comportou ao longo do tempo.