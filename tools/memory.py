# pyrefly: ignore [missing-import]
from fastmcp import FastMCP
from tools.db import execute_query, execute_insert
from tools.clients import _get_client_internal

mcp = FastMCP("memory")

@mcp.tool()
def add_user_memory(cpf: str, fact: str) -> dict:
    """Adiciona um fato ou preferencia na memoria de longo prazo do cliente."""
    client = _get_client_internal(cpf)
    if not client:
        return {"error": f"Cliente com CPF {cpf} não encontrado."}
    
    sql = "INSERT INTO user_memory (client_id, fact) VALUES (%s, %s) RETURNING *"
    res = execute_insert(sql, (client["id"], fact))
    return res[0] if res else {}

@mcp.tool()
def get_user_context(cpf: str) -> list:
    """Recupera todos os fatos e memorias de longo prazo armazenados sobre o cliente."""
    client = _get_client_internal(cpf)
    if not client:
        return []
    res = execute_query("SELECT fact FROM user_memory WHERE client_id = %s", (client["id"],))
    return [item["fact"] for item in res]
