# pyrefly: ignore [missing-import]
from fastmcp import FastMCP
from tools.db import execute_query, execute_insert
from tools.clients import _get_client_internal
from tools.advisor import analisar_fluxo_caixa
from tools.audit import log_action

mcp = FastMCP("transactions")

NECESSITY_KEYWORDS = {
    "alimentação": ("feira", "mercado", "supermercado", "alimento", "comida"),
    "moradia": ("aluguel", "condomínio", "energia", "luz", "água", "gás"),
    "saúde": ("farmácia", "remédio", "consulta", "exame", "hospital"),
    "transporte": ("combustível", "gasolina", "ônibus", "transporte", "uber"),
    "educação": ("curso", "faculdade", "escola", "livro didático"),
    "comunicação": ("internet", "telefone", "plano móvel"),
    "manutenção": ("conserto", "concerto", "reparo", "manutenção"),
}

WISH_KEYWORDS = {
    "lazer": ("streaming", "netflix", "spotify", "cinema", "show", "passeio"),
    "restaurantes": ("restaurante", "delivery", "ifood", "lanche"),
    "compras pessoais": ("roupa", "calçado", "tênis", "perfume", "acessório"),
}

FUTURE_KEYWORDS = {
    "investimento": ("investimento", "aporte", "tesouro", "cdb", "ação", "etf"),
    "reserva": ("reserva de emergência", "reserva"),
    "poupança": ("poupança",),
}


def categorizar_transacao(category: str, description: str) -> str:
    """Normaliza a categoria usando a descrição como evidência principal."""
    texto = f"{category or ''} {description or ''}".lower()
    categoria_normalizada = (category or "").strip()
    categorias_permitidas = {
        "alimentação", "moradia", "saúde", "transporte", "educação",
        "comunicação", "tecnologia", "manutenção", "seguros", "impostos",
        "dívidas", "cuidados pessoais", "dependentes", "lazer",
        "entretenimento", "restaurantes", "compras pessoais", "viagens",
        "hobbies", "presentes", "doações", "investimento", "reserva",
        "poupança", "aposentadoria",
    }

    # Uma categoria canônica e específica escolhida com contexto pelo agente
    # prevalece sobre heurísticas textuais.
    if categoria_normalizada.lower() in categorias_permitidas:
        return categoria_normalizada.title()

    for categoria, palavras in FUTURE_KEYWORDS.items():
        if any(palavra in texto for palavra in palavras):
            return categoria.title()

    for categoria, palavras in NECESSITY_KEYWORDS.items():
        if any(palavra in texto for palavra in palavras):
            return categoria.title()

    for categoria, palavras in WISH_KEYWORDS.items():
        if any(palavra in texto for palavra in palavras):
            return categoria.title()

    return "Outros"


@mcp.tool()
def add_transaction(cpf: str, amount: float, category: str, description: str, date: str, installments: int = 1, status: str = 'paid', is_recurring: bool = False) -> dict:
    """Registra um gasto ou conta. Envie uma categoria específica por item; nunca agrupe despesas diferentes como 'Compras'."""
    client = _get_client_internal(cpf)
    if not client:
        return {"error": f"Cliente com CPF {cpf} não encontrado."}
        
    if amount < 0:
        return {"error": "ERRO DE SEGURANÇA: O valor (amount) não pode ser negativo. Transações devem ser registradas com valor absoluto positivo. Corrija o parâmetro e tente novamente."}
    
    if status.lower() == 'pendente': status = 'pending'
    elif status.lower() == 'pago': status = 'paid'

    category = categorizar_transacao(category, description)

    sql = """INSERT INTO transactions (client_id, amount, installments, category, description, transaction_date, status, is_recurring)
             VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING *"""
    res = execute_insert(sql, (client["id"], amount, installments, category, description, date, status, is_recurring))

    if res:
        log_action("TRANSACTION_CREATED", cpf, {
            "transaction_id": res[0].get("id"),
            "amount": amount,
            "category": category,
            "status": status,
            "transaction_date": date,
            "installments": installments,
            "is_recurring": is_recurring,
        })

    return {
        "status": "success",
        "transacao_registrada": res[0] if res else {},
        "fluxo_de_caixa_atualizado": analisar_fluxo_caixa(cpf)
    }

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
    current = execute_query(
        "SELECT category, description FROM transactions WHERE id = %s",
        (transaction_id,),
        fetch_one=True,
    )
    current_data = current[0] if current else {}
    if amount is not None:
        if amount < 0:
            return {"error": "ERRO DE SEGURANÇA: O valor (amount) não pode ser negativo. Transações devem ser registradas com valor absoluto positivo. Corrija o parâmetro e tente novamente."}
        updates.append("amount = %s")
        params.append(amount)
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

    # Toda atualização também revisa a categoria. Isso corrige registros antigos
    # classificados genericamente como "Compras", mesmo quando só o valor mudou.
    description_for_category = description if description is not None else current_data.get("description", "")
    category_for_normalization = category if category is not None else current_data.get("category", "")
    normalized_category = categorizar_transacao(category_for_normalization, description_for_category)
    if normalized_category and normalized_category != current_data.get("category"):
        updates.append("category = %s")
        params.append(normalized_category)
        
    if not updates:
        return {"error": "Nenhum dado fornecido para atualização."}
        
    sql = f"UPDATE transactions SET {', '.join(updates)} WHERE id = %s RETURNING *"
    params.append(transaction_id)
    
    res = execute_insert(sql, tuple(params))
    
    # precisamos recuperar o cpf do client_id para atualizar o fluxo

    
    cpf_cliente = None
    if res:
        client_data = execute_query("SELECT cpf FROM clients WHERE id = %s", (res[0]["client_id"],), fetch_one=True)
        if client_data:
            cpf_cliente = client_data[0]["cpf"]
            log_action("TRANSACTION_UPDATED", cpf_cliente, {
                "transaction_id": transaction_id,
                "changed_fields": [field.split(" = ")[0] for field in updates],
                "amount": res[0].get("amount"),
                "category": res[0].get("category"),
                "status": res[0].get("status"),
            })
            
    return {
        "status": "success",
        "transacao_atualizada": res[0] if res else {},
        "fluxo_de_caixa_atualizado": analisar_fluxo_caixa(cpf_cliente) if cpf_cliente else None
    } if res else {"error": "Transação não encontrada ou falha ao atualizar."}

@mcp.tool()
def delete_transaction(transaction_id: str) -> dict:
    """Exclui permanentemente uma transação ou conta a pagar do banco de dados pelo seu ID."""
    # Busca o client_id antes de deletar

    
    cpf_cliente = None
    trans = execute_query("SELECT client_id FROM transactions WHERE id = %s", (transaction_id,), fetch_one=True)
    if trans:
        client_data = execute_query("SELECT cpf FROM clients WHERE id = %s", (trans[0]["client_id"],), fetch_one=True)
        if client_data:
            cpf_cliente = client_data[0]["cpf"]

    sql = "DELETE FROM transactions WHERE id = %s RETURNING id"
    res = execute_insert(sql, (transaction_id,))

    if res and cpf_cliente:
        log_action("TRANSACTION_DELETED", cpf_cliente, {
            "transaction_id": transaction_id,
        })
    
    return {
        "status": "success", 
        "deleted_id": transaction_id,
        "fluxo_de_caixa_atualizado": analisar_fluxo_caixa(cpf_cliente) if cpf_cliente else None
    } if res else {"error": "Falha ao excluir ou transação não encontrada."}
