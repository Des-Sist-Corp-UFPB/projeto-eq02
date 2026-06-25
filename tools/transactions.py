# pyrefly: ignore [missing-import]
from fastmcp import FastMCP
from tools.db import execute_query, execute_insert
from tools.clients import _get_client_internal

mcp = FastMCP("transactions")

@mcp.tool()
def add_transaction(cpf: str, amount: float, category: str, description: str, date: str, installments: int = 1, status: str = 'paid', is_recurring: bool = False) -> dict:
    """Registra uma transacao (gasto) ou uma conta a pagar para o cliente. Use status='pending' para contas futuras."""
    client = _get_client_internal(cpf)
    if not client:
        return {"error": f"Cliente com CPF {cpf} não encontrado."}
        
    if amount < 0:
        return {"error": "ERRO DE SEGURANÇA: O valor (amount) não pode ser negativo. Transações devem ser registradas com valor absoluto positivo. Corrija o parâmetro e tente novamente."}
    
    if status.lower() == 'pendente': status = 'pending'
    elif status.lower() == 'pago': status = 'paid'

    sql = """INSERT INTO transactions (client_id, amount, installments, category, description, transaction_date, status, is_recurring)
             VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING *"""
    res = execute_insert(sql, (client["id"], amount, installments, category, description, date, status, is_recurring))
    return res[0] if res else {}

@mcp.tool()
def query_transactions(cpf: str, month: int = None, year: int = None, status: str = None) -> list:
    """Retorna as transacoes (gastos) e contas a pagar do cliente. Você pode filtrar por mês e ano e status ('paid' para gastos, 'pending' para contas a pagar)."""
    client = _get_client_internal(cpf)
    if not client:
        return []
    
    sql = "SELECT * FROM transactions WHERE client_id = %s"
    params = [client["id"]]
    
    if month:
        sql += " AND EXTRACT(MONTH FROM transaction_date) = %s"
        params.append(month)
    if year:
        sql += " AND EXTRACT(YEAR FROM transaction_date) = %s"
        params.append(year)
    if status:
        if status.lower() == 'pendente': status = 'pending'
        elif status.lower() == 'pago': status = 'paid'
        sql += " AND status = %s"
        params.append(status)
        
    sql += " ORDER BY transaction_date ASC"
    
    return execute_query(sql, tuple(params))

@mcp.tool()
def update_transaction(transaction_id: str, amount: float = None, category: str = None, description: str = None, date: str = None, installments: int = None, status: str = None, is_recurring: bool = None) -> dict:
    """Atualiza uma transação ou conta existente. Permite marcar uma conta como paga alterando o status para 'paid'. O agente deve usar query_transactions para encontrar o transaction_id antes de atualizar."""
    updates = []
    params = []
    if amount is not None:
        if amount < 0:
            return {"error": "ERRO DE SEGURANÇA: O valor (amount) não pode ser negativo. Transações devem ser registradas com valor absoluto positivo. Corrija o parâmetro e tente novamente."}
        updates.append("amount = %s")
        params.append(amount)
    if category is not None:
        updates.append("category = %s")
        params.append(category)
    if description is not None:
        updates.append("description = %s")
        params.append(description)
    if date is not None:
        updates.append("transaction_date = %s")
        params.append(date)
    if installments is not None:
        updates.append("installments = %s")
        params.append(installments)
    if status is not None:
        updates.append("status = %s")
        params.append(status)
    if is_recurring is not None:
        updates.append("is_recurring = %s")
        params.append(is_recurring)
        
    if not updates:
        return {"error": "Nenhum dado fornecido para atualização."}
        
    sql = f"UPDATE transactions SET {', '.join(updates)} WHERE id = %s RETURNING *"
    params.append(transaction_id)
    
    res = execute_insert(sql, tuple(params))
    return res[0] if res else {"error": "Transação não encontrada ou falha ao atualizar."}

@mcp.tool()
def delete_transaction(transaction_id: str) -> dict:
    """Exclui permanentemente uma transação ou conta a pagar do banco de dados pelo seu ID."""
    sql = "DELETE FROM transactions WHERE id = %s RETURNING id"
    res = execute_insert(sql, (transaction_id,))
    return {"status": "success", "deleted_id": transaction_id} if res else {"error": "Falha ao excluir ou transação não encontrada."}