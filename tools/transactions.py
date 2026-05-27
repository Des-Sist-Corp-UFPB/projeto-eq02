# pyrefly: ignore [missing-import]
from fastmcp import FastMCP
from tools.db import supabase
from tools.clients import _get_client_internal

mcp = FastMCP("transactions")

@mcp.tool()
def add_transaction(cpf: str, amount: float, category: str, description: str, date: str, installments: int = 1) -> dict:
    """Registra uma transacao ou gasto financeiro para o cliente."""
    client = _get_client_internal(cpf)
    if not client:
        return {"error": f"Cliente com CPF {cpf} não encontrado."}
    
    data = {
        "client_id": client["id"],
        "amount": amount,
        "installments": installments,
        "category": category,
        "description": description,
        "transaction_date": date
    }
    response = supabase.table("transactions").insert(data).execute()
    if response.data:
        return response.data[0]
    return {}

@mcp.tool()
def query_transactions(cpf: str) -> list:
    """Retorna o historico completo de transacoes e gastos de um cliente pelo seu CPF."""
    client = _get_client_internal(cpf)
    if not client:
        return []
    
    response = supabase.table("transactions").select("*").eq("client_id", client["id"]).order("transaction_date", desc=True).execute()
    return response.data

@mcp.tool()
def update_transaction(transaction_id: str, amount: float = None, category: str = None, description: str = None, date: str = None, installments: int = None) -> dict:
    """Atualiza uma transação (gasto) existente. Permite corrigir valores, categorias, descrição, data ou número de parcelas. O agente deve usar query_transactions para encontrar o transaction_id antes de atualizar."""
    update_data = {}
    if amount is not None: update_data["amount"] = amount
    if category is not None: update_data["category"] = category
    if description is not None: update_data["description"] = description
    if date is not None: update_data["transaction_date"] = date
    if installments is not None: update_data["installments"] = installments
    
    if not update_data:
        return {"error": "Nenhum dado fornecido para atualização."}
        
    response = supabase.table("transactions").update(update_data).eq("id", transaction_id).execute()
    if response.data:
        return response.data[0]
    return {"error": "Transação não encontrada ou falha ao atualizar."}
