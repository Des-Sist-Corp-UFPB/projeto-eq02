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

