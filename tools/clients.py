# pyrefly: ignore [missing-import]
from fastmcp import FastMCP
from typing import Optional
from tools.db import execute_query, execute_insert

mcp = FastMCP("clients")

def _get_client_internal(cpf: str) -> Optional[dict]:
    """Helper interno para não dar conflito com o proxy do MCP."""
    res = execute_query("SELECT * FROM clients WHERE cpf = %s", (cpf,), fetch_one=True)
    return res[0] if res else None

@mcp.tool()
def get_client_info(cpf: str) -> Optional[dict]:
    """Busca as informacoes cadastrais e renda de um cliente pelo seu CPF."""
    return _get_client_internal(cpf)

@mcp.tool()
def register_client(nome: str, cpf: str, email: str, renda_total: float) -> dict:
    """Cadastra um novo cliente."""
    sql = """INSERT INTO clients (nome, cpf, email, renda_total) 
             VALUES (%s, %s, %s, %s) RETURNING *"""
    res = execute_insert(sql, (nome, cpf, email, renda_total))
    return res[0] if res else {}

@mcp.tool()
def atualizar_renda(cpf: str, nova_renda: float) -> dict:
    """Atualiza a renda mensal base do cliente no banco de dados."""
    client = _get_client_internal(cpf)
    if not client: return {"error": "Cliente não encontrado"}
    sql = "UPDATE clients SET renda_total = %s WHERE cpf = %s RETURNING *"
    res = execute_insert(sql, (nova_renda, cpf))
    return res[0] if res else {}

@mcp.tool()
def obter_roteiro_atendimento(cpf: str) -> str:
    """Obtém o roteiro exato de como o assistente deve se comportar e o que deve falar na primeira mensagem do chat."""
    client = _get_client_internal(cpf)
    if not client:
        return "Cliente não encontrado. Peça desculpas e peça para ele verificar o login."
    
    nome = client.get("nome", "Cliente")
    renda = float(client.get("renda_total", 0.0))
    
    if renda == 0.0:
        return f"""
        ROTEIRO PARA NOVO USUÁRIO (Renda não cadastrada):
        1. Dê boas-vindas muito amigáveis e informais chamando-o pelo nome: {nome}.
        2. Diga que está animado para ajudar a organizar as finanças usando a Regra 50/30/20.
        3. Pergunte, de forma natural, duas coisas para começarmos: "Qual a sua renda mensal atual?" e "Quais são os seus maiores objetivos/metas para o futuro?" (ex: quitar dívidas, viajar, comprar casa).
        4. Diga que usará as metas dele para aconselhar no fluxo de caixa no dia a dia.
        5. PARE de gerar texto. Aguarde ele responder com as informações.
        """
    else:
        return f"""
        ROTEIRO PARA USUÁRIO EXISTENTE (Renda cadastrada de R$ {renda}):
        1. Dê boas-vindas amigáveis chamando-o pelo nome: {nome}.
        2. (Se for o caso, use a tool de memória para lembrar de algo).
        3. Pergunte: 'Como posso te ajudar hoje? Registrar um novo gasto, dar uma olhada no fluxo de caixa deste mês, ou simular um investimento?'
        """
