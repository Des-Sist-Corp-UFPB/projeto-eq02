from unittest.mock import patch

from tools.investment_research import (
    MAX_RESEARCH_SOURCES,
    TRUSTED_DOMAINS,
    _extract_sources,
    _load_investment_guide,
    _research_investments,
)


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


def test_extract_sources_limits_and_prioritizes_citations():
    payload = {
        "search_sources": [
            {"title": "Fonte de busca", "url": "https://bcb.gov.br/busca"}
        ],
        "annotations": [
            {
                "type": "url_citation",
                "title": f"Fonte {index}",
                "url": f"https://bcb.gov.br/fonte-{index}",
            }
            for index in range(MAX_RESEARCH_SOURCES + 5)
        ],
    }

    sources = _extract_sources(payload)

    assert len(sources) == MAX_RESEARCH_SOURCES
    assert sources[0]["url"] == "https://bcb.gov.br/fonte-0"
    assert all(source["url"] != "https://bcb.gov.br/busca" for source in sources)


def test_load_investment_guide():
    guide = _load_investment_guide()
    assert "# Guia-base de investimentos" in guide
    assert "Não existe investimento universalmente melhor" in guide


@patch("tools.investment_research.OpenAI")
def test_research_uses_web_search_and_trusted_domains(mock_openai):
    mock_openai.return_value.responses.create.return_value = FakeResponse()
    result = _research_investments(800.0, 12, "reserva", "conservador")

    assert result["status"] == "ok"
    assert result["query"]["valor"] == 800.0
    assert result["knowledge_base"]["loaded"] is True
    assert result["sources"][0]["url"] == "https://www.bcb.gov.br/teste"

    kwargs = mock_openai.return_value.responses.create.call_args.kwargs
    assert kwargs["tool_choice"] == "required"
    assert kwargs["tools"][0]["filters"]["allowed_domains"] == TRUSTED_DOMAINS
    assert kwargs["include"] == ["web_search_call.action.sources"]
    assert "<guia_local>" in kwargs["input"]
    assert "Não existe investimento universalmente melhor" in kwargs["input"]


def test_research_rejects_invalid_values():
    assert "error" in _research_investments(0, 12, "", "")
    assert "error" in _research_investments(800, 0, "", "")
