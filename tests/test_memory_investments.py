from unittest.mock import patch

from tools.memory import get_investment_history, save_investment_choice


@patch("tools.memory.log_action")
@patch("tools.memory.execute_insert")
@patch("tools.memory._get_client_internal")
def test_save_investment_choice(mock_client, mock_insert, mock_log):
    mock_client.return_value = {"id": "client-1"}
    mock_insert.return_value = [{"id": "memory-1"}]

    result = save_investment_choice("123", "Tesouro Selic", 800.0, "2026-08-06")

    assert result == {
        "status": "success",
        "investment_name": "Tesouro Selic",
        "amount": 800.0,
        "investment_date": "2026-08-06",
    }
    fact = mock_insert.call_args.args[1][1]
    assert "nome=Tesouro Selic" in fact
    assert "valor=800.00" in fact
    mock_log.assert_called_once()


@patch("tools.memory._get_client_internal")
def test_save_investment_choice_requires_name(mock_client):
    mock_client.return_value = {"id": "client-1"}
    result = save_investment_choice("123", "   ")
    assert "error" in result


@patch("tools.memory.execute_query")
@patch("tools.memory._get_client_internal")
def test_get_investment_history(mock_client, mock_query):
    mock_client.return_value = {"id": "client-1"}
    mock_query.return_value = [{
        "fact": "INVESTIMENTO_ESCOLHIDO | data=2026-08-06 | nome=CDB 110% do CDI | valor=800.00",
        "created_at": "2026-08-06T20:00:00Z",
    }]

    result = get_investment_history("123")

    assert result[0]["investment_name"] == "CDB 110% do CDI"
    assert result[0]["amount"] == 800.0
    assert result[0]["investment_date"] == "2026-08-06"
