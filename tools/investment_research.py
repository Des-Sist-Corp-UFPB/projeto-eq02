"""Pesquisa web atualizada para apoiar orientacoes de investimento."""

from datetime import datetime, timezone
import logging
import os
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from openai import OpenAI


logger = logging.getLogger(__name__)
mcp = FastMCP("investment_research")
MAX_RESEARCH_SOURCES = 10

GUIDE_PATH = (
    Path(__file__).resolve().parents[1]
    / "wiki"
    / "04-regras-de-negocio"
    / "guia-investimentos.md"
)

TRUSTED_DOMAINS = [
    "bcb.gov.br",
    "tesourodireto.com.br",
    "gov.br",
    "cvm.gov.br",
    "b3.com.br",
    "fgc.org.br",
    "anbima.com.br",
]


def _load_investment_guide() -> str:
    """Carrega a base local versionada usada para orientar a pesquisa."""
    guide = GUIDE_PATH.read_text(encoding="utf-8").strip()
    if not guide:
        raise ValueError("O guia-base de investimentos esta vazio.")
    return guide


def _extract_sources(response: Any) -> list[dict[str, str]]:
    """Prioriza fontes citadas, remove duplicatas e limita a resposta."""
    payload = response.model_dump() if hasattr(response, "model_dump") else response
    sources: list[dict[str, str]] = []
    seen: set[str] = set()

    def visit(value: Any, citations_only: bool) -> None:
        if len(sources) >= MAX_RESEARCH_SOURCES:
            return
        if isinstance(value, dict):
            url = value.get("url")
            is_citation = value.get("type") == "url_citation"
            if (
                isinstance(url, str)
                and url.startswith(("https://", "http://"))
                and url not in seen
                and (is_citation or not citations_only)
            ):
                seen.add(url)
                sources.append({
                    "title": str(value.get("title") or value.get("name") or url),
                    "url": url,
                })
            for nested in value.values():
                visit(nested, citations_only)
        elif isinstance(value, (list, tuple)):
            for nested in value:
                visit(nested, citations_only)

    visit(payload, citations_only=True)
    if not sources:
        visit(payload, citations_only=False)
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

    try:
        investment_guide = _load_investment_guide()
    except (OSError, UnicodeError, ValueError) as exc:
        logger.exception("Falha ao carregar o guia-base de investimentos")
        return {
            "status": "error",
            "consulted_at": consulted_at,
            "message": "A base local de investimentos nao esta disponivel.",
            "error_type": type(exc).__name__,
        }

    prompt = f"""
Use o GUIA LOCAL abaixo como regra de interpretacao e seguranca. Complemente-o
com dados atuais encontrados na web. Informacoes atuais da web prevalecem apenas
para taxas, datas, limites e regras que possam ter mudado.

<guia_local>
{investment_guide}
</guia_local>

Pesquise alternativas de investimento disponiveis no Brasil para este cenario:
- aporte inicial unico: R$ {valor:.2f};
- prazo: {prazo_meses} meses;
- objetivo declarado: {objetivo.strip() or 'nao informado'};
- perfil de risco declarado: {perfil_risco.strip() or 'nao informado'}.

Use no máximo {MAX_RESEARCH_SOURCES} fontes institucionais permitidas, escolhendo
somente as mais diretamente relevantes para a comparação. Compare alternativas adequadas
ao prazo usando dados atuais encontrados, como taxa de referencia, liquidez,
tributacao, garantia, riscos e data-base. Nao invente uma rentabilidade nem trate
retorno passado como promessa. Nao escolha um produto como "o melhor": apresente
exatamente 5 alternativas reais e comparaveis e explique as condicoes em que cada uma faz
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
        "knowledge_base": {
            "document": "wiki/04-regras-de-negocio/guia-investimentos.md",
            "loaded": True,
        },
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
