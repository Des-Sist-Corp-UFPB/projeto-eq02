# pyrefly: ignore [missing-import]
from fastmcp import FastMCP
from typing import Optional, Dict
from datetime import datetime, timedelta
from tools.clients import _get_client_internal
from tools.db import execute_query

mcp = FastMCP("advisor")

@mcp.tool()
def simular_investimento(valor_mensal: float, meses: int, taxa_anual_porcentagem: float = 10.0) -> dict:
    """Calcula o montante final de um investimento com aportes mensais usando juros compostos."""
    taxa_mensal = (taxa_anual_porcentagem / 100) / 12
    montante = 0.0
    for _ in range(meses):
        montante = (montante + valor_mensal) * (1 + taxa_mensal)
    return {"montante_final": round(montante, 2), "total_investido": round(valor_mensal * meses, 2)}

@mcp.tool()
def sugerir_investimentos(saldo_livre: float) -> dict:
    """Retorna opções de investimentos e rentabilidades baseadas no saldo livre informado."""
    if saldo_livre <= 0:
        return {"recomendacao": "No momento, o foco deve ser organizar as contas e sair do vermelho antes de investir."}
    
    if saldo_livre <= 500:
        opcoes = [
            {"tipo": "Tesouro Selic", "prazo": "Curto Prazo / Reserva", "rentabilidade_esperada": "~10.5% ao ano", "risco": "Baixíssimo"},
            {"tipo": "CDB 100% CDI Liquidez Diária", "prazo": "Curto Prazo / Reserva", "rentabilidade_esperada": "~10.4% ao ano", "risco": "Baixo (Garantia FGC)"}
        ]
    elif saldo_livre <= 2000:
        opcoes = [
            {"tipo": "Tesouro IPCA+", "prazo": "Médio Prazo", "rentabilidade_esperada": "Inflação + ~6% ao ano", "risco": "Baixo"},
            {"tipo": "CDBs Prefixados", "prazo": "Médio Prazo (1 a 3 anos)", "rentabilidade_esperada": "~11% a 12% ao ano", "risco": "Baixo"},
            {"tipo": "FIIs (Fundos Imobiliários)", "prazo": "Longo Prazo / Renda Passiva", "rentabilidade_esperada": "Dividendos de ~0.8% a 1% ao mês", "risco": "Médio (Renda Variável)"}
        ]
    else:
        opcoes = [
            {"tipo": "Tesouro IPCA+", "prazo": "Longo Prazo / Aposentadoria", "rentabilidade_esperada": "Inflação + ~6% ao ano", "risco": "Baixo"},
            {"tipo": "ETFs Globais (ex: WRLD11)", "prazo": "Longo Prazo", "rentabilidade_esperada": "Acompanha mercado global", "risco": "Alto (Renda Variável)"},
            {"tipo": "Carteira de FIIs e Ações", "prazo": "Longo Prazo", "rentabilidade_esperada": "Dividendos mensais + Valorização", "risco": "Médio/Alto"}
        ]
        
    return {
        "analise": f"Com um saldo livre de R$ {saldo_livre:.2f}, você tem boas opções para rentabilizar seu dinheiro.",
        "opcoes_sugeridas": opcoes,
        "dica": "Lembre-se: antes de investir em renda variável ou opções presas, construa sua Reserva de Emergência (3 a 6 meses do seu custo de vida) com liquidez diária!"
    }

@mcp.tool()
def analisar_fluxo_caixa(cpf: str) -> dict:
    """Analisa os gastos focando apenas nas parcelas ou despesas integrais que incidem no mês vigente."""
    client = _get_client_internal(cpf)
    if not client: return {"error": "Cliente não encontrado"}
    
    renda = float(client.get("renda_total", 0.0))
    hoje = datetime.now()
    
    # Puxa todas as transações, pois compras de meses passados podem ter parcelas caindo neste mês
    res = execute_query("SELECT * FROM transactions WHERE client_id = %s", (client["id"],))
    
    total_gasto = 0.0
    total_pendente = 0.0
    gastos_por_categoria: Dict[str, float] = {}
    
    if res:
        for t in res:
            t_date_val = t["transaction_date"]
            if isinstance(t_date_val, str):
                t_date = datetime.strptime(t_date_val, "%Y-%m-%d")
            else:
                t_date = t_date_val
            installments = int(t.get("installments") or 1)
            amount = float(t["amount"])
            status = t.get("status", "paid")
            
            # Calcula quantos meses se passaram desde a compra
            diff_months = (hoje.year - t_date.year) * 12 + (hoje.month - t_date.month)
            
            # Se a diferença de meses for maior ou igual a 0 e menor que o número de parcelas, a parcela incide neste mês
            if 0 <= diff_months < installments:
                valor_parcela = amount / installments
                
                if status == 'pending':
                    total_pendente += valor_parcela
                else:
                    total_gasto += valor_parcela
                    gastos_por_categoria[t["category"]] = gastos_por_categoria.get(t["category"], 0.0) + valor_parcela
                
    burn_rate = (total_gasto / renda * 100) if renda > 0 else 0.0
            
    return {
        "mes_analisado": hoje.strftime("%Y-%m"),
        "renda_mensal": renda,
        "total_gasto_mes_atual": round(total_gasto, 2),
        "total_contas_pendentes": round(total_pendente, 2),
        "saldo_livre_projetado": round(renda - total_gasto - total_pendente, 2),
        "burn_rate_porcentagem": round(burn_rate, 2),
        "gastos_por_categoria": {k: round(v, 2) for k, v in gastos_por_categoria.items()}
    }
