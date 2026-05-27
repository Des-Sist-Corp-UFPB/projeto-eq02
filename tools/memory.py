# pyrefly: ignore [missing-import]
from fastmcp import FastMCP
from tools.db import supabase
from tools.clients import _get_client_internal

mcp = FastMCP("memory")

@mcp.tool()
def add_user_memory(cpf: str, fact: str) -> dict:
    """Adiciona um fato ou preferencia na memoria de longo prazo do cliente."""
    client = _get_client_internal(cpf)
    if not client:
        return {"error": f"Cliente com CPF {cpf} não encontrado."}
    
    data = {
        "client_id": client["id"],
        "fact": fact
    }
    response = supabase.table("user_memory").insert(data).execute()
    if response.data:
        return response.data[0]
    return {}

@mcp.tool()
def get_user_context(cpf: str) -> list:
    """Recupera todos os fatos e memorias de longo prazo armazenados sobre o cliente."""
    client = _get_client_internal(cpf)
    if not client:
        return []
    response = supabase.table("user_memory").select("fact").eq("client_id", client["id"]).execute()
    return [item["fact"] for item in response.data]
