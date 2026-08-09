# 04 - Regras de Negócio (Core)

## Autenticação e Sessão
*   O identificador global do usuário no sistema é o **CPF**. 
*   No fluxo de Login, os cookies nativos do Chainlit (`access_token` e `session_id`) são forçadamente excluídos pela API para evitar travamentos, repassando o estado via `auth_cpf` e JWT personalizado (`auth_token`).

## Regras Financeiras Principais
1.  **Regra 50/30/20**: O cálculo das parcelas deve OBRIGATORIAMENTE ser realizado com base na **renda total (bruta)** do usuário, salva no cadastro. Nunca deve ser aplicado sobre saldos residuais (dinheiro que sobrou no mês).
2.  **Unificação de Lógica Analítica**: O resumo de fluxo de caixa (total gasto, contas pendentes e categorias) é servido de forma única por `analisar_fluxo_caixa` (em `tools/advisor.py`). O LLM está estritamente instruído a nunca realizar deduções matemáticas baseadas em mensagens, usando sempre essa função.
3.  **Rate Limiting**: O usuário não pode enviar mais do que 10 mensagens no período de 60 segundos no Chat (`chat_app.py`).

## Controle de Experiência Híbrida (UI Control)
A visibilidade do Dashboard é controlada de forma reativa e autônoma:
*   Se o usuário acionar termos como "investimento", "simular" ou a IA invocar ferramentas afins, a flag de visibilidade no `state.py` vira `False` e o painel analítico se esconde.
*   Se lidar com fluxo de caixa, contas ou transações, a flag vira `True` e o dashboard financeiro se expande.
