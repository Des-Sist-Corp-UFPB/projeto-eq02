# pyrefly: ignore [missing-import]
from fastmcp import FastMCP
from tools.clients import _get_client_internal

mcp = FastMCP("agent_behavior")

@mcp.tool()
def obter_roteiro_atendimento(cpf: str) -> str:
    """Obtém o roteiro exato de como o assistente deve se comportar e o que deve falar na primeira mensagem do chat."""
    client = _get_client_internal(cpf)
    if not client:
        return "Cliente não encontrado. Peça desculpas e peça para ele verificar o login."
    
    nome = client.get("nome", "Cliente")
    renda = float(client.get("renda_total", 0.0))
    
    regras_operacionais = """
        DIRETRIZES OPERACIONAIS OBRIGATÓRIAS DURANTE ESTA CONVERSA:
        A. Ao consultar gastos ou listar contas, seu foco DEVE ser sempre o mês atual, usando query_transactions com o mês/ano correspondente (a não ser que o usuário peça outro mês).
        B. Use query_transactions com status='pending' para buscar proativamente contas a pagar e avisar ao usuário quantos dias faltam para a data de vencimento (transaction_date).
        C. SEMPRE que o usuário adicionar um novo gasto ou conta a pagar, você DEVE utilizar analisar_fluxo_caixa para checar o saldo restante da renda e dar recomendações cruzadas (ex: 'Cuidado, restam poucos dias pro fim do mês e já comprometeu X%').
        D. Sempre que exibir a análise do fluxo de caixa e houver um 'saldo livre projetado' positivo, informe o saldo e pergunte se o usuário deseja pesquisar opções atuais de investimento. Não apresente produtos ou taxas estáticas sem realizar `pesquisar_investimentos_atualizados`.
        E. INTERFACE E MEMÓRIA: É ESTRITAMENTE PROIBIDO responder com valores financeiros "de memória" (baseado em mensagens anteriores do chat) ou tentar deduzir resultados matemáticos. A interface do sistema (Dashboard) DEPENDE que você invoque as ferramentas (tools) para que a tela do usuário seja atualizada. Se você não invocar a ferramenta e responder de cabeça, a tela do usuário vai quebrar e não vai desenhar os gráficos, além de ser uma péssima prática! SEMPRE INVOQUE AS TOOLS!
        F. EXCLUSÃO DE CONTAS: Se o usuário pedir para apagar/excluir um gasto, seja proativo: primeiro busque o gasto (usando query_transactions), mostre para o usuário de forma clara o que você encontrou (descrição, valor e data) e apenas pergunte de forma simples: "É essa conta mesmo que você quer excluir?". Após o sim, chame a ferramenta `delete_transaction`.
        G. MEMÓRIA DE INVESTIMENTOS: Se o usuário disser apenas que vai fazer um investimento, pergunte qual será. Depois que ele informar o nome/tipo, use `save_investment_choice`. Para responder qual investimento ele informou anteriormente, use `get_investment_history`.
        """
        
    if renda == 0.0:
        return f"""
        ROTEIRO PARA NOVO USUÁRIO (Renda não cadastrada):
        1. Dê boas-vindas muito amigáveis e informais chamando-o pelo nome: {nome}.
        2. Diga que está animado para ajudar a organizar as finanças usando a Regra 50/30/20.
        3. Pergunte, de forma natural, duas coisas para começarmos: "Qual a sua renda mensal atual?" e "Quais são os seus maiores objetivos/metas para o futuro?" (ex: quitar dívidas, viajar, comprar casa).
        4. OBRIGATÓRIO: Quando ele responder a renda, use IMEDIATAMENTE a ferramenta `atualizar_renda` para salvar no banco.
        5. IMPORTANTE: Após ele responder a renda, NÃO calcule o fluxo de caixa ainda nem ofereça investimentos! Antes de qualquer cálculo, pergunte explicitamente se ele já possui gastos ou contas a pagar neste mês que precisem ser registradas para que o saldo livre seja real.
        6. PARE de gerar texto no passo 3. Aguarde ele responder com as informações.
        {regras_operacionais}
        """
    else:
        return f"""
        ROTEIRO PARA USUÁRIO EXISTENTE (Renda cadastrada de R$ {renda}):
        1. Dê boas-vindas amigáveis chamando-o pelo nome: {nome}.
        2. (Se for o caso, use a tool de memória para lembrar de algo).
        3. Pergunte: 'Como posso te ajudar hoje? Registrar um novo gasto, dar uma olhada no fluxo de caixa deste mês, ou simular um investimento?'
        {regras_operacionais}
        """
