# pyrefly: ignore [missing-import]
import pytest
from unittest.mock import patch, MagicMock

# Cobertura de api_server
from fastapi.testclient import TestClient
from api_server import app, DashboardStateRequest, TransactionInput, LoginRequest, RegisterRequest

def test_api_server_routes():
    client = TestClient(app)
    
    # Frontend Routes
    assert client.get("/").status_code == 200 # Redirect followed by default
    assert client.get("/hibrido").status_code == 200
    assert client.get("/dashboard").status_code == 200
    
    # Dashboard data sem autenticação
    assert client.get("/api/dashboard_data").status_code == 401
    
    # Models coverage (instanciar pydantic models para cobrir)
    req = DashboardStateRequest(cpf="123", state=True)
    assert req.cpf == "123"
    
    req2 = TransactionInput(category="Food", amount=10, description="Pizza", status="paid")
    assert req2.amount == 10

    req3 = RegisterRequest(nome="Joao", cpf="123", email="joao@email.com", password="123")
    assert req3.nome == "Joao"
    
    req4 = LoginRequest(cpf="123", password="123")
    assert req4.cpf == "123"

@patch("api_server.DASHBOARD_STATES", {"123": {"view": "metas", "sim_data": {"a": 1}, "tool_name": "test_tool"}})
@patch("tools.advisor.analisar_fluxo_caixa")
def test_dashboard_data_success(mock_analisar):
    client = TestClient(app)
    mock_analisar.return_value = {
        "renda_mensal": 5000,
        "total_gasto_mes_atual": 2000,
        "saldo_livre_projetado": 3000,
        "total_contas_pendentes": 500,
        "gastos_por_categoria": {"Alimentação": 1000}
    }
    
    # Send request with cookie
    response = client.get("/api/dashboard_data", cookies={"auth_cpf": "123"})
    assert response.status_code == 200
    data = response.json()
    assert data["view"] == "metas"
    assert data["renda"] == 5000
    assert data["categorias"][0]["categoria"] == "Alimentação"

@patch("tools.advisor.analisar_fluxo_caixa")
def test_dashboard_data_error(mock_analisar):
    client = TestClient(app)
    mock_analisar.return_value = {"error": "Usuário não encontrado"}
    response = client.get("/api/dashboard_data", cookies={"auth_cpf": "123"})
    assert response.status_code == 404
