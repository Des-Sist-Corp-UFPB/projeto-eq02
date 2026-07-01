# Ideia de Servidor MCP — EQ02

**Domínio:** Assistente financeiro pessoal (já usa LangGraph+OpenAI)  
**Data:** 2026-07-01

## O que é

Um **servidor MCP (Model Context Protocol)** expõe as operações do seu sistema como *tools* e *resources* que qualquer assistente de IA (Claude Desktop, Cursor, etc.) pode chamar com segurança. Na prática, é uma camada fina sobre a **API que vocês já têm** — cada tool chama um endpoint/service existente. Assim o projeto deixa de ser só uma tela e passa a ser operável por um agente de IA.

## Servidor proposto: `financia-mcp`

### Tools sugeridas

- `lancar_gasto(valor, categoria, data)` — registra um gasto
- `consultar_saldo()` — saldo e burn rate
- `resumo_50_30_20()` — análise da regra 50/30/20
- `checar_metas()` — metas de categoria rompidas

### Resources (somente leitura)

- extrato mensal como resource

### Exemplos de uso com um LLM

- "Gastei 50 no ifood hoje" → lança o gasto
- "Como está minha regra 50/30/20 esse mês?"

## Esqueleto para começar (Python / FastMCP)

```python
# pip install mcp httpx
from mcp.server.fastmcp import FastMCP
import httpx

mcp = FastMCP("financia-mcp")
API = "http://localhost:8000"   # sua API local (ajuste a porta)

@mcp.tool()
def lancar_gasto(valor, categoria, data):
    """registra um gasto"""
    r = httpx.get(f"{API}/seu/endpoint")   # reaproveite sua API existente
    return r.json()

if __name__ == "__main__":
    mcp.run()   # transporte stdio; registre no Claude Desktop / Cursor
```

## Boas práticas

- **Segurança:** cada tool que altera dados deve exigir autenticação e registrar no **log de auditoria** (o mesmo do requisito da disciplina).
- **Escopo mínimo:** exponha só o necessário; separe tools de leitura das de escrita.
- **Reaproveite:** as tools devem chamar seus *services*/*controllers* existentes, não reimplementar regra de negócio.

## Referências
- Documentação MCP: https://modelcontextprotocol.io
- SDKs: Python (`mcp`), TypeScript (`@modelcontextprotocol/sdk`), Java (Spring AI MCP Server).

*Sugestão gerada em 2026-07-01 para orientar a integração de LLMs ao projeto.*