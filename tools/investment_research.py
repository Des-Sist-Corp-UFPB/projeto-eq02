"""Pesquisa web atualizada para apoiar orientacoes de investimento."""

from datetime import datetime, timezone
import logging
import os
from typing import Any

from fastmcp import FastMCP
from openai import OpenAI


logger = logging.getLogger(__name__)
mcp = FastMCP("investment_research")

TRUSTED_DOMAINS = [
    "bcb.gov.br",
    "tesourodireto.com.br",
    "gov.br",
    "cvm.gov.br",
    "b3.com.br",
    "fgc.org.br",
    "anbima.com.br",
]


def _extract_sources(response: Any) -> list[dict[str, str]]:
    """Extrai e remove duplicatas das URLs retornadas pela busca web."""
    payload = response.model_dump() if hasattr(response, "model_dump") else response
    sources: list[dict[str, str]] = []
    seen: set[str] = set()

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            url = value.get("url")
            if isinstance(url, str) and url.startswith(("https://", "http://")) and url not in seen:
                seen.add(url)
                sources.append({
                    "title": str(value.get("title") or value.get("name") or url),
                    "url": url,
                })
            for nested in value.values():
                visit(nested)
        elif isinstance(value, (list, tuple)):
            for nested in value:
                visit(nested)

    visit(payload)
    return sources


def _research_investments(
    valor: float,
    prazo_meses: int,
    objetivo: str,
    perfil_risco: str,
) -> dict[str, Any]:
    if valor <= 0:
        return {"error": "Informe um valor de investimento maior que zero."}
    if prazo_meses <= 0 or prazo_meses > 600:
        return {"error": "O prazo deve estar entre 1 e 600 meses."}

    consulted_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    model = os.getenv("OPENAI_WEB_SEARCH_MODEL", "gpt-5.6")
    prompt = f"""
Pesquise alternativas de investimento disponiveis no Brasil para este cenario:
- aporte inicial unico: R$ {valor:.2f};
- prazo: {prazo_meses} meses;
- objetivo declarado: {objetivo.strip() or 'nao informado'};
- perfil de risco declarado: {perfil_risco.strip() or 'nao informado'}.

Use somente as fontes institucionais permitidas. Compare alternativas adequadas
ao prazo usando dados atuais encontrados, como taxa de referencia, liquidez,
tributacao, garantia, riscos e data-base. Nao invente uma rentabilidade nem trate
retorno passado como promessa. Nao escolha um produto como "o melhor": apresente
de 2 a 5 alternativas comparaveis e explique as condicoes em que cada uma faz
sentido. Quando uma taxa exata nao estiver disponivel, diga isso claramente.

Responda em portugues do Brasil, de forma concisa, com estas secoes:
1. Cenario consultado
2. Alternativas encontradas
3. Taxas/dados utilizaveis em simulacao
4. Riscos e ressalvas
Inclua citacoes junto das afirmacoes factuais.
""".strip()

    try:
        response = OpenAI().responses.create(
            model=model,
            tools=[{
                "type": "web_search",
                "filters": {"allowed_domains": TRUSTED_DOMAINS},
            }],
            tool_choice="required",
            include=["web_search_call.action.sources"],
            input=prompt,
        )
    except Exception as exc:
        logger.exception("Falha ao pesquisar investimentos na web")
        return {
            "status": "error",
            "consulted_at": consulted_at,
            "message": "Nao foi possivel consultar as fontes financeiras agora. Tente novamente em instantes.",
            "error_type": type(exc).__name__,
        }

    return {
        "status": "ok",
        "consulted_at": consulted_at,
        "model": model,
        "query": {
            "valor": round(valor, 2),
            "prazo_meses": prazo_meses,
            "objetivo": objetivo,
            "perfil_risco": perfil_risco,
        },
        "report": response.output_text,
        "sources": _extract_sources(response),
        "disclaimer": (
            "Conteudo educacional baseado em informacoes publicas; nao constitui "
            "recomendacao individual nem garantia de rentabilidade."
        ),
    }


@mcp.tool()
def pesquisar_investimentos_atualizados(
    valor: float,
    prazo_meses: int = 12,
    objetivo: str = "",
    perfil_risco: str = "",
) -> dict[str, Any]:
    """Pesquisa opcoes atuais no Brasil em fontes institucionais.

    Use antes de sugerir investimentos quando a pergunta depender do mercado,
    de taxas ou de produtos atuais. O valor representa um aporte inicial unico.
    """
    return _research_investments(valor, prazo_meses, objetivo, perfil_risco)

