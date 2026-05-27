# 🗺️ Roadmap e Próximos Passos (FinancIA's)

Este documento descreve as próximas grandes funcionalidades e evoluções planejadas para o projeto, visando torná-lo um consultor financeiro ainda mais completo e pronto para produção.

## 1. Módulo de RAG para Investimentos (Retrieval-Augmented Generation)
**Objetivo:** Transformar o agente em um especialista avançado em investimentos.
- **Integração de Conhecimento:** O agente será capaz de ler e extrair dados de sites de finanças, relatórios de mercado e PDFs (ex: carteiras recomendadas, análises de fundos).
- **Respostas Embasadas:** Em vez de depender apenas do conhecimento pré-treinado do LLM, o agente buscará o contexto mais atualizado em uma base de dados vetorial (utilizando o `pgvector` já previsto no Supabase) antes de responder dúvidas sobre onde investir.

## 2. Dashboard Financeiro Interativo (Visão de Produção)
**Objetivo:** Oferecer uma visão analítica tradicional além da interface conversacional.
- **Nova Interface (Aba Separada):** Criação de uma aba de "Painel/Dashboard" no front-end.
- **Gráficos e Indicadores:** Visualização gráfica do fluxo de caixa, divisão da regra 50/30/20, evolução de metas e projeção de juros compostos.
- **Produção:** Esta feature focará em entregar uma experiência de aplicativo financeiro completo para o usuário final, complementando o chat inteligente.