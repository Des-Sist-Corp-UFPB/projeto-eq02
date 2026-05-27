# pyrefly: ignore [missing-import]
from fastmcp import FastMCP
from tools.db import execute_query, execute_insert
from tools.clients import _get_client_internal

mcp = FastMCP("goals")

@mcp.tool()
def set_goal(cpf: str, category: str, limit_amount: float, month_year: str) -> dict:
    """Define uma meta de limite de gastos mensais para uma categoria especifica."""
    client = _get_client_internal(cpf)
    if not client:
        return {"error": f"Cliente com CPF {cpf} não encontrado."}
    
    sql = """INSERT INTO goals (client_id, category, limit_amount, month_year) 
             VALUES (%s, %s, %s, %s) RETURNING *"""
    res = execute_insert(sql, (client["id"], category, limit_amount, month_year))
    return res[0] if res else {}

@mcp.tool()
def check_goal_status(cpf: str) -> list:
    """Retorna todas as metas de limite de gastos definidas para o cliente."""
    client = _get_client_internal(cpf)
    if not client:
        return []
    return execute_query("SELECT * FROM goals WHERE client_id = %s", (client["id"],))
