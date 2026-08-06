# pyrefly: ignore [missing-import]
from fastmcp import FastMCP
from tools.db import execute_query, execute_insert
from tools.clients import _get_client_internal
from tools.audit import log_action
from datetime import date
from typing import Optional

mcp = FastMCP("memory")

@mcp.tool()
def add_user_memory(cpf: str, fact: str) -> dict:
    """Adiciona um fato ou preferencia na memoria de longo prazo do cliente."""
    client = _get_client_internal(cpf)
    if not client:
        return {"error": f"Cliente com CPF {cpf} não encontrado."}
    
    sql = "INSERT INTO user_memory (client_id, fact) VALUES (%s, %s) RETURNING *"
    res = execute_insert(sql, (client["id"], fact))
    if res:
        log_action("MEMORY_CREATED", cpf, {
            "memory_id": res[0].get("id"),
            "content_stored": True,
        })
    return res[0] if res else {}

@mcp.tool()
def get_user_context(cpf: str) -> list:
    """Recupera todos os fatos e memorias de longo prazo armazenados sobre o cliente."""
    client = _get_client_internal(cpf)
    if not client:
        return []
    res = execute_query("SELECT fact FROM user_memory WHERE client_id = %s", (client["id"],))
    return [item["fact"] for item in res]


INVESTMENT_MEMORY_PREFIX = "INVESTIMENTO_ESCOLHIDO"


@mcp.tool()
def save_investment_choice(
    cpf: str,
    investment_name: str,
    amount: Optional[float] = None,
    investment_date: str = "",
) -> dict:
    """Salva qual investimento o cliente afirmou que fará ou realizou.

    Só use depois que o cliente informar explicitamente o nome/tipo do
    investimento. Se ele disser apenas que vai investir, pergunte qual será.
    """
    client = _get_client_internal(cpf)
    if not client:
        return {"error": f"Cliente com CPF {cpf} não encontrado."}

    investment_name = " ".join((investment_name or "").split())
    if not investment_name:
        return {"error": "Informe qual foi o investimento escolhido."}
    if amount is not None and amount <= 0:
        return {"error": "O valor do investimento deve ser maior que zero."}

    chosen_date = investment_date.strip() or date.today().isoformat()
    amount_text = f"{amount:.2f}" if amount is not None else "nao_informado"
    fact = (
        f"{INVESTMENT_MEMORY_PREFIX} | data={chosen_date} | "
        f"nome={investment_name} | valor={amount_text}"
    )

    sql = "INSERT INTO user_memory (client_id, fact) VALUES (%s, %s) RETURNING *"
    res = execute_insert(sql, (client["id"], fact))
    if not res:
        return {"error": "Não foi possível salvar a escolha de investimento."}

    log_action("INVESTMENT_CHOICE_SAVED", cpf, {
        "memory_id": res[0].get("id"),
        "investment_name": investment_name,
        "amount": amount,
        "investment_date": chosen_date,
    })
    return {
        "status": "success",
        "investment_name": investment_name,
        "amount": amount,
        "investment_date": chosen_date,
    }


@mcp.tool()
def get_investment_history(cpf: str) -> list[dict]:
    """Recupera, do mais recente ao mais antigo, investimentos informados pelo cliente."""
    client = _get_client_internal(cpf)
    if not client:
        return []

    rows = execute_query(
        """SELECT fact, created_at FROM user_memory
           WHERE client_id = %s AND fact LIKE %s
           ORDER BY created_at DESC""",
        (client["id"], f"{INVESTMENT_MEMORY_PREFIX}%"),
    )

    history = []
    for row in rows or []:
        fields = {}
        for part in row["fact"].split(" | ")[1:]:
            key, separator, value = part.partition("=")
            if separator:
                fields[key] = value

        amount_text = fields.get("valor", "nao_informado")
        history.append({
            "investment_name": fields.get("nome", "Não informado"),
            "amount": None if amount_text == "nao_informado" else float(amount_text),
            "investment_date": fields.get("data"),
            "saved_at": row.get("created_at"),
        })

    return history
