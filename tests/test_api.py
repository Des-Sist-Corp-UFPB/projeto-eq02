from unittest.mock import patch
from fastapi.testclient import TestClient

def test_ping(client: TestClient):
    """Teste básico para verificar se o healthcheck simples está respondendo."""
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "timestamp" in response.json()

def test_health(client: TestClient):
    """Teste para verificar se o healthcheck detalhado está respondendo."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["ok"] is True

def test_dashboard_data_unauthorized(client: TestClient):
    """Teste para verificar bloqueio na rota autenticada se não houver cookie."""
    response = client.get("/api/dashboard_data")
    assert response.status_code == 401
    assert response.json()["detail"] == "Não autenticado"

@patch("api_server.execute_query")
def test_login_invalid(mock_query, client: TestClient):
    """Teste de login com credenciais inválidas (banco não encontra cpf)."""
    # Configura o mock do banco para retornar vazio (usuário não encontrado)
    mock_query.return_value = []
    
    response = client.post("/login", json={"cpf": "12345678901", "password": "wrong"})
    assert response.status_code == 401
    assert response.json()["detail"] == "CPF ou Senha inválidos."

@patch("api_server.execute_query")
@patch("api_server.verify_password")
def test_login_success(mock_verify, mock_query, client: TestClient):
    """Teste de login bem-sucedido."""
    # Configura o mock do banco para retornar um usuário válido
    mock_query.return_value = [{"cpf": "12345678901", "password_hash": "hashed_pw"}]
    # Configura o mock de senha para aprovar a senha
    mock_verify.return_value = True
    
    response = client.post("/login", json={"cpf": "12345678901", "password": "correct"})
    assert response.status_code == 200
    assert response.json()["message"] == "Login efetuado com sucesso!"
    
    # Verifica se os cookies foram setados
    assert "auth_token" in response.cookies
    assert "auth_cpf" in response.cookies
