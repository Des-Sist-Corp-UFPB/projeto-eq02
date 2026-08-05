from unittest.mock import patch

from tools.investment_research import TRUSTED_DOMAINS, _extract_sources, _research_investments


class FakeResponse:
    output_text = "Relatorio atualizado com citacoes."

    def model_dump(self):
        return {
            "output": [{
                "type": "web_search_call",
                "action": {
                    "sources": [
                        {"title": "Banco Central", "url": "https://www.bcb.gov.br/teste"},
                        {"title": "Duplicada", "url": "https://www.bcb.gov.br/teste"},
                    ]
                },
            }]
        }


def test_extract_sources_remove_duplicatas():
    assert _extract_sources(FakeResponse()) == [{
        "title": "Banco Central",
        "url": "https://www.bcb.gov.br/teste",
    }]


@patch("tools.investment_research.OpenAI")
def test_research_uses_web_search_and_trusted_domains(mock_openai):
    mock_openai.return_value.responses.create.return_value = FakeResponse()
    result = _research_investments(800.0, 12, "reserva", "conservador")

    assert result["status"] == "ok"
    assert result["query"]["valor"] == 800.0
    assert result["sources"][0]["url"] == "https://www.bcb.gov.br/teste"

    kwargs = mock_openai.return_value.responses.create.call_args.kwargs
    assert kwargs["tool_choice"] == "required"
    assert kwargs["tools"][0]["filters"]["allowed_domains"] == TRUSTED_DOMAINS
    assert kwargs["include"] == ["web_search_call.action.sources"]


def test_research_rejects_invalid_values():
    assert "error" in _research_investments(0, 12, "", "")
    assert "error" in _research_investments(800, 0, "", "")
