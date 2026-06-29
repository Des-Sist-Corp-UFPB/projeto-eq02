# pyrefly: ignore [missing-import]
import pytest
from unittest.mock import patch
from tools.audit import log_action

@patch("tools.audit.execute_insert")
def test_log_action_success(mock_execute_insert):
    """Testa se log_action chama o execute_insert com os parâmetros corretos."""
    log_action("LOGIN_SUCCESS", "12345678901", {"ip": "127.0.0.1"})
    
    mock_execute_insert.assert_called_once()
    args = mock_execute_insert.call_args[0]
    
    assert args[1][0] == "LOGIN_SUCCESS"
    assert args[1][1] == "12345678901"
    assert '{"ip": "127.0.0.1"}' in args[1][2]

@patch("tools.audit.execute_insert")
def test_log_action_without_details(mock_execute_insert):
    """Testa se log_action funciona corretamente sem o argumento details."""
    log_action("REGISTER", "12345678901")
    
    mock_execute_insert.assert_called_once()
    args = mock_execute_insert.call_args[0]
    
    assert args[1][2] == "{}"

@patch("tools.audit.execute_insert")
def test_log_action_exception(mock_execute_insert, capsys):
    """Testa se log_action lida com exceções sem quebrar o sistema."""
    mock_execute_insert.side_effect = Exception("Database error")
    
    log_action("TEST_ERROR", "111")
    
    captured = capsys.readouterr()
    assert "Erro ao registrar auditoria: Database error" in captured.out
