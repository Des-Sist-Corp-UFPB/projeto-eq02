# pyrefly: ignore [missing-import]
import pytest
from unittest.mock import patch
from tools.advisor import simular_investimento, sugerir_investimentos, analisar_fluxo_caixa

def test_simular_investimento():
    res = simular_investimento(100.0, 12, 10.0)
    assert "montante_final" in res
    assert "total_investido" in res
    assert res["total_investido"] == 100.0
    assert res["montante_final"] > 100.0
    assert res["projecao_mensal"]["total_aportado"] == [100.0] * 13
    assert res["projecao_mensal"]["meses"] == list(range(13))
    assert len(res["projecao_mensal"]["opcoes"][0]["valores"]) == 13

def test_sugerir_investimentos_zero():
    res = sugerir_investimentos(0.0)
    assert "não é suficiente" in res["recomendacao"]

def test_sugerir_investimentos_baixo():
    res = sugerir_investimentos(300.0)
    assert "analise_estrategica" in res
    assert len(res["opcoes_sugeridas"]) == 2
    assert len(res["projecao_mensal"]["opcoes"]) == 2
    assert len(res["projecao_mensal"]["meses"]) == 13

def test_sugerir_investimentos_medio():
    res = sugerir_investimentos(1000.0)
    assert len(res["opcoes_sugeridas"]) == 3

def test_sugerir_investimentos_alto():
    res = sugerir_investimentos(5000.0)
    assert len(res["opcoes_sugeridas"]) == 3

@patch("tools.advisor._get_client_internal")
def test_sugerir_investimentos_inteligente(mock_client):
    mock_client.return_value = {"renda_total": 5000.0}
    res = sugerir_investimentos(1500.0, aplicar_regra_inteligente=True, cpf="123")
    assert "analise_estrategica" in res
    
@patch("tools.advisor._get_client_internal")
def test_sugerir_investimentos_inteligente_pouco_valor(mock_client):
    mock_client.return_value = {"renda_total": 5000.0}
    res = sugerir_investimentos(200.0, aplicar_regra_inteligente=True, cpf="123")
    assert "analise_estrategica" in res

@patch("tools.advisor._get_client_internal")
def test_analisar_fluxo_caixa_nao_encontrado(mock_client):
    mock_client.return_value = None
    res = analisar_fluxo_caixa("123")
    assert "error" in res

@patch("tools.advisor._get_client_internal")
@patch("tools.advisor.execute_query")
def test_analisar_fluxo_caixa_encontrado(mock_query, mock_client):
    mock_client.return_value = {"id": "client_id", "renda_total": 5000.0}
    from datetime import datetime
    hoje_str = datetime.now().strftime("%Y-%m-%d")
    mock_query.return_value = [
        {"transaction_date": hoje_str, "installments": 1, "amount": 100.0, "status": "paid", "category": "Alimentação"},
        {"transaction_date": hoje_str, "installments": 1, "amount": 50.0, "status": "pending", "category": "Transporte"}
    ]
    res = analisar_fluxo_caixa("123")
    assert res["renda_mensal"] == 5000.0
    assert res["total_gasto_mes_atual"] == 100.0
    assert res["total_contas_pendentes"] == 50.0
