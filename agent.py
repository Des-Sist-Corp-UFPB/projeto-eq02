import os
from typing import TypedDict, Annotated
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

# Bibliotecas oficiais do MCP
# pyrefly: ignore [missing-import]
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

def add_messages(left: list, right: list):
    return left + right

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    cpf_ativo: str

# Variáveis globais para manter o cliente e o agente vivos
_agent_app = None
_mcp_client = None

async def get_agent_app():
    """Inicializa a conexão MCP com o servidor e compila o LangGraph de forma assíncrona."""
    global _agent_app, _mcp_client
    
    if _agent_app is not None:
        return _agent_app

    # Inicializa o Cliente MCP que vai se comunicar com o mcp_server.py via Subprocesso (Stdio)
    _mcp_client = MultiServerMCPClient(
        {
            "finance_server": {
                "command": "python",
                "args": ["mcp_server.py"],
                "transport": "stdio",
                "env": dict(os.environ)
            }
        },
        tool_name_prefix=False
    )
    
    # 🌟 Mágica do MCP: O LangChain pergunta ao servidor quais ferramentas ele tem
    # e já converte todas elas para o formato do LangChain automaticamente!
    tools = await _mcp_client.get_tools()
    
    # Conecta as ferramentas dinâmicas ao LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    llm_with_tools = llm.bind_tools(tools)
    
    def chatbot(state: AgentState):
        cpf = state.get("cpf_ativo")
        if not cpf:
            cpf = "ERRO_SEM_CPF"
            
        sys_msg = SystemMessage(content=f"""
Você é o Assistente Financeiro Inteligente.
O CPF do cliente logado é {cpf}. SEMPRE use esse CPF para chamar as ferramentas.

Diretrizes obrigatórias:
1. Sempre verifique as metas de gastos (verificar_metas) APÓS registrar um novo gasto. Se a meta foi ultrapassada, dê um alerta claro e rigoroso.
2. Seja proativo e consultivo: utilize analisar_fluxo_caixa para avaliar se o cliente está gastando demais no mês.
3. Utilize a regra 50/30/20 (50% necessidades, 30% desejos, 20% futuro) para dar conselhos.
4. Utilize recuperar_contexto_memoria no inicio da conversa para lembrar de informações anteriores e tornar a experiência pessoal.
5. Quando simular investimentos, não dê apenas os números. Aja como um consultor educador:
   - Para prazos curtos (até 2 anos) ou Reserva de Emergência: sugira opções de Renda Fixa com liquidez diária (Tesouro Selic, CDBs 100% CDI).
   - Para prazos médios/longos (mais de 3 anos): explique opções que protegem contra inflação (Tesouro IPCA+) e introduza conceitos básicos de Renda Variável (ETFs globais como WRLD11, FIIs para dividendos).
   - Ensine *como* começar (ex: 'Abra conta em uma corretora taxa zero, transfira o dinheiro e busque pelo título...').
6. Você deve agir como um parceiro financeiro, amigável mas responsável.
""")
        messages = [sys_msg] + state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    # Construção do fluxo do LangGraph
    graph_builder = StateGraph(AgentState)
    graph_builder.add_node("chatbot", chatbot)
    
    tool_node = ToolNode(tools=tools)
    graph_builder.add_node("tools", tool_node)
    
    graph_builder.add_conditional_edges("chatbot", tools_condition)
    graph_builder.add_edge("tools", "chatbot")
    graph_builder.set_entry_point("chatbot")
    
    memory = MemorySaver()
    _agent_app = graph_builder.compile(checkpointer=memory)
    
    return _agent_app