# pyrefly: ignore [missing-import]
from fastmcp import FastMCP
from typing import Optional, Dict
from datetime import datetime, timedelta
import time
import logging
from opentelemetry import trace
from tools.clients import _get_client_internal
from tools.db import execute_query

tracer = trace.get_tracer("advisor")
logger = logging.getLogger(__name__)

mcp = FastMCP("advisor")

@mcp.tool()
def simular_investimento(valor_mensal: float, meses: int, taxa_anual_porcentagem: float = 10.0) -> dict:
    """Calcula o montante final de um investimento com aportes mensais usando juros compostos."""
    import json
    taxa_mensal = (taxa_anual_porcentagem / 100) / 12
    montante = 0.0
    investido = 0.0
    hist_montante = []
    hist_investido = []
    
    for _ in range(meses):
        investido += valor_mensal
        montante = (montante + valor_mensal) * (1 + taxa_mensal)
        hist_montante.append(round(montante, 2))
        hist_investido.append(round(investido, 2))
        
    return {
        "montante_final": round(montante, 2), 
        "total_investido": round(investido, 2),
        "dica": "Explique de forma resumida o resultado da simulação para o usuário. Não há gráficos, use apenas texto."
    }

@mcp.tool()
def sugerir_investimentos(valor: float, aplicar_regra_inteligente: bool = False, cpf: str = "", meses_simulacao: int = 12) -> dict:
    """
    Retorna opções de investimentos e rentabilidades projetadas.
    - OBRIGATÓRIO: Se o usuário disser EXPLICITAMENTE um valor para investir (ex: "quero investir 500", "tenho 500 reais para investir"), você DEVE passar aplicar_regra_inteligente=False e valor=500. Neste caso, NÃO tente adaptar ou calcular frações.
    - OBRIGATÓRIO: SÓ passe aplicar_regra_inteligente=True se o usuário pedir algo genérico como "o que faço com o meu dinheiro que sobrou?", "sugira investimentos", "onde invisto?". Nesse caso, passe como 'valor' o saldo livre total que ele tem no fluxo de caixa atual. Você DEVE fornecer o 'cpf' neste caso.
    """
    if valor <= 0:
        return {"recomendacao": "O valor informado não é suficiente para realizar aportes."}
        
    if aplicar_regra_inteligente:
        renda = 0.0
        if cpf:
            client = _get_client_internal(cpf)
            if client:
                renda = float(client.get("renda_total", 0.0))
                
        meta_ideal = renda * 0.20
        
        if renda > 0 and valor >= meta_ideal:
            valor_mensal = meta_ideal
            reserva = valor - valor_mensal
            analise_estrategica = f"Seu salário é R$ {renda:.2f} e você tem R$ {valor:.2f} livres. A meta (20% da renda) é R$ {meta_ideal:.2f}. Como você tem folga, foquei a simulação na meta ideal e ainda te deixei R$ {reserva:.2f} para imprevistos e lazer."
        else:
            valor_mensal = valor * 0.40
            reserva = valor * 0.60
            if renda > 0:
                analise_estrategica = f"A meta ideal seria R$ {meta_ideal:.2f} (20% da sua renda), mas como seu saldo livre atual é R$ {valor:.2f}, precisei adaptar a estratégia. Reservei 60% (R$ {reserva:.2f}) para o seu dia a dia e foquei em investir os 40% restantes (R$ {valor_mensal:.2f})."
            else:
                analise_estrategica = f"Dos R$ {valor:.2f} livres no mês, reservei inteligentemente 60% (R$ {reserva:.2f}) para imprevistos. As simulações abaixo usam os 40% restantes (R$ {valor_mensal:.2f}) para investimentos."
    else:
        valor_mensal = valor
        analise_estrategica = f"Com aportes fixos de R$ {valor_mensal:.2f} por {meses_simulacao} meses, eis as projeções para algumas carteiras de investimentos:"
    
    if valor_mensal <= 500:
        opcoes = [
            {"tipo": "Tesouro Selic", "prazo": "Curto Prazo / Reserva", "taxa_anual": 10.5, "rentabilidade_esperada": "~10.5% ao ano", "risco": "Baixíssimo"},
            {"tipo": "CDB 100% CDI Liquidez Diária", "prazo": "Curto Prazo / Reserva", "taxa_anual": 10.4, "rentabilidade_esperada": "~10.4% ao ano", "risco": "Baixo (Garantia FGC)"}
        ]
    elif valor_mensal <= 2000:
        opcoes = [
            {"tipo": "Tesouro IPCA+", "prazo": "Médio Prazo", "taxa_anual": 10.5, "rentabilidade_esperada": "Inflação + ~6% ao ano", "risco": "Baixo"},
            {"tipo": "CDBs Prefixados", "prazo": "Médio Prazo (1 a 3 anos)", "taxa_anual": 11.5, "rentabilidade_esperada": "~11% a 12% ao ano", "risco": "Baixo"},
            {"tipo": "FIIs (Fundos Imobiliários)", "prazo": "Longo Prazo / Renda Passiva", "taxa_anual": 11.0, "rentabilidade_esperada": "Dividendos de ~0.8% a 1% ao mês", "risco": "Médio (Renda Variável)"}
        ]
    else:
        opcoes = [
            {"tipo": "Tesouro IPCA+ Longo", "prazo": "Longo Prazo / Aposentadoria", "taxa_anual": 10.5, "rentabilidade_esperada": "Inflação + ~6% ao ano", "risco": "Baixo"},
            {"tipo": "ETFs Globais (ex: WRLD11)", "prazo": "Longo Prazo", "taxa_anual": 15.0, "rentabilidade_esperada": "Acompanha mercado global", "risco": "Alto (Renda Variável)"},
            {"tipo": "Carteira de FIIs e Ações", "prazo": "Longo Prazo", "taxa_anual": 12.0, "rentabilidade_esperada": "Dividendos mensais + Valorização", "risco": "Médio/Alto"}
        ]
        
    labels = []
    valores = []
    valor_investido_puro = valor_mensal * meses_simulacao
    
    for op in opcoes:
        taxa_mensal = (op["taxa_anual"] / 100) / 12
        montante = 0.0
        for _ in range(meses_simulacao):
            montante = (montante + valor_mensal) * (1 + taxa_mensal)
        
        labels.append(op["tipo"])
        valores.append(round(montante, 2))
        op["simulacao_final_projetada"] = f"R$ {montante:.2f} (em {meses_simulacao} meses)"
        # Remove a taxa interna para não confundir o LLM
        del op["taxa_anual"]
        
    return {
        "analise_estrategica": analise_estrategica,
        "opcoes_sugeridas": opcoes,
        "dica": "ATENÇÃO: Foque apenas em explicar textualmente as opções de forma clara."
    }

@mcp.tool()
def analisar_fluxo_caixa(cpf: str) -> dict:
    """Analisa os gastos focando apenas nas parcelas ou despesas integrais que incidem no mês vigente."""
    with tracer.start_as_current_span("analise-fluxo-caixa-50-30-20") as span:
        span.set_attribute("usuario.cpf", cpf)
        logger.info("Iniciando análise de fluxo de caixa", extra={"usuario.cpf": cpf, "acao": "analisar_fluxo"})
        time.sleep(0.5) # Gargalo proposital para o trace de 500ms
        
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
        "gastos_por_categoria": {k: round(v, 2) for k, v in gastos_por_categoria.items()},
        "regra_50_30_20": {
            "Necessidades": round(sum(v for k, v in gastos_por_categoria.items() if k in ['Moradia', 'Alimentação', 'Saúde', 'Transporte', 'Educação']), 2),
            "Desejos": round(sum(v for k, v in gastos_por_categoria.items() if k not in ['Moradia', 'Alimentação', 'Saúde', 'Transporte', 'Educação', 'Investimento', 'Reserva', 'Poupança']), 2),
            "Futuro": round(sum(v for k, v in gastos_por_categoria.items() if k in ['Investimento', 'Reserva', 'Poupança']), 2)
        }
    }
