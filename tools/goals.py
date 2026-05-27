# pyrefly: ignore [missing-import]
from fastmcp import FastMCP
from tools.db import supabase
from tools.clients import _get_client_internal

mcp = FastMCP("goals")

@mcp.tool()
def set_goal(cpf: str, category: str, limit_amount: float, month_year: str) -> dict:
    """Define uma meta de limite de gastos mensais para uma categoria especifica."""
    client = _get_client_internal(cpf)
    if not client:
        return {"error": f"Cliente com CPF {cpf} não encontrado."}
    
    data = {
        "client_id": client["id"],
        "category": category,
        "limit_amount": limit_amount,
        "month_year": month_year
    }
    response = supabase.table("goals").insert(data).execute()
    if response.data:
        return response.data[0]
    return {}

@mcp.tool()
def check_goal_status(cpf: str) -> list:
    """Retorna todas as metas de limite de gastos definidas para o cliente."""
    client = _get_client_internal(cpf)
    if not client:
        return []
    response = supabase.table("goals").select("*").eq("client_id", client["id"]).execute()
    return response.data
