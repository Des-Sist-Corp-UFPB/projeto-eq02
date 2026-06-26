# pyrefly: ignore [missing-import]
from fastmcp import FastMCP
from dotenv import load_dotenv

from tools.clients import mcp as clients_mcp
from tools.transactions import mcp as transactions_mcp
from tools.goals import mcp as goals_mcp
from tools.memory import mcp as memory_mcp
from tools.advisor import mcp as advisor_mcp
from tools.agent_behavior import mcp as behavior_mcp
from tools.security import mcp as security_mcp

load_dotenv()

mcp = FastMCP(
    "finance_assistant",
    instructions=(
        "Servidor MCP do Assistente Financeiro Inteligente com Memória Real. "
        "Guardrails obrigatórios: "
        "(1) Nunca registre gastos ou acesse o histórico sem confirmar de qual cliente estamos falando (use o cpf). "
        "(2) Se o limite de gastos para uma categoria for ultrapassado após adicionar uma transação, notifique o cliente imediatamente com um alerta financeiro. "
        "(3) Utilize a memória de longo prazo para personalizar o atendimento com as informações aprendidas sobre o cliente. "
        "(4) Ao avaliar as finanças do cliente, use a renda_total do cadastro para dar dicas proporcionais e coerentes com a realidade dele."
    ),
)

mcp.mount(clients_mcp, prefix="clients")
mcp.mount(transactions_mcp, prefix="transactions")
mcp.mount(goals_mcp, prefix="goals")
mcp.mount(memory_mcp, prefix="memory")
mcp.mount(advisor_mcp, prefix="advisor")
mcp.mount(behavior_mcp, prefix="behavior")
mcp.mount(security_mcp, prefix="security")

@mcp.tool()
def help() -> str:
    """Lista todas as ferramentas disponíveis neste servidor MCP e suas descrições."""
    tools = mcp.get_tools()
    lines = [f"- `{name}`: {tool.description}" for name, tool in tools.items()]
    return "\n".join(lines)

if __name__ == "__main__":
    mcp.run(transport="sse")