import chainlit as cl
from typing import Optional
from agent import get_agent_app
from langchain_core.messages import HumanMessage
import uuid
import os
import json
import re
import plotly.graph_objects as go
from openai import AsyncOpenAI

openai_client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

from tools.security import mask_cpf, verificar_output_guardrails


def extrair_payload_tool(tool_message):
    """Converte o conteúdo de uma mensagem de tool em dicionário."""
    content = (
        tool_message.get("content")
        if isinstance(tool_message, dict)
        else getattr(tool_message, "content", None)
    )
    if isinstance(content, dict):
        payload = content
    elif isinstance(content, list):
        text_blocks = [
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        try:
            payload = json.loads("".join(text_blocks))
        except (json.JSONDecodeError, TypeError):
            return None
    elif isinstance(content, str):
        try:
            payload = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            return None
    else:
        return None

    return payload if isinstance(payload, dict) else None


def extrair_projecao_investimento(tool_message):
    """Extrai a série mensal estruturada devolvida por uma tool de investimento."""
    payload = extrair_payload_tool(tool_message)
    if not payload:
        return None

    projection = payload.get("projecao_mensal")
    if not isinstance(projection, dict):
        return None
    if not projection.get("meses") or not projection.get("opcoes"):
        return None
    return projection


def combinar_projecoes_investimento(current, new):
    """Acumula todas as opções calculadas durante a mesma mensagem do usuário."""
    if current is None:
        return {
            "meses": list(new["meses"]),
            "total_aportado": list(new.get("total_aportado", [])),
            "opcoes": list(new["opcoes"]),
        }

    if current["meses"] != new["meses"]:
        return new

    existing_names = {option["nome"] for option in current["opcoes"]}
    for option in new["opcoes"]:
        if option["nome"] not in existing_names:
            current["opcoes"].append(option)
            existing_names.add(option["nome"])
    return current


def remover_detalhamento_mensal(response: str) -> str:
    """Remove do texto os pontos mensais que já são exibidos no gráfico."""
    cleaned_lines = []
    monthly_value = re.compile(r"^\s*(?:[-*]\s*)?(?:\*\*)?m[eê]s\s+\d+\s*:", re.IGNORECASE)
    monthly_heading = re.compile(r"^\s*(?:\*\*)?proje[cç][aã]o\s+mensal\s*:", re.IGNORECASE)

    for line in response.splitlines():
        if monthly_value.match(line) or monthly_heading.match(line):
            continue
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


def criar_grafico_investimentos(projection):
    """Monta um gráfico interativo comparando todas as projeções retornadas."""
    months = projection["meses"]
    figure = go.Figure()

    figure.add_trace(go.Scatter(
        x=months,
        y=projection.get("total_aportado", []),
        mode="lines",
        name="Capital inicial",
        line={"color": "#94a3b8", "width": 2, "dash": "dash"},
        hovertemplate="Mês %{x}<br>Capital investido: R$ %{y:,.2f}<extra></extra>",
    ))

    colors = ["#38bdf8", "#a78bfa", "#34d399", "#fbbf24", "#fb7185"]
    for index, option in enumerate(projection["opcoes"]):
        figure.add_trace(go.Scatter(
            x=months,
            y=option["valores"],
            mode="lines+markers",
            name=option["nome"],
            line={"color": colors[index % len(colors)], "width": 3},
            marker={"size": 5},
            hovertemplate=f"{option['nome']}<br>Mês %{{x}}: R$ %{{y:,.2f}}<extra></extra>",
        ))

    figure.update_layout(
        title={"text": "Evolução projetada dos investimentos", "x": 0.02},
        xaxis_title="Mês",
        yaxis_title="Saldo acumulado (R$)",
        hovermode="x unified",
        template="plotly_dark",
        paper_bgcolor="#111827",
        plot_bgcolor="#111827",
        legend={"orientation": "h", "y": -0.24, "x": 0},
        margin={"l": 55, "r": 25, "t": 60, "b": 90},
        height=560,
    )
    figure.update_xaxes(dtick=1, gridcolor="rgba(148,163,184,0.12)")
    figure.update_yaxes(gridcolor="rgba(148,163,184,0.12)", tickprefix="R$ ")
    return figure

# Esta função intercepta o cookie de login definido pelo nosso FastAPI
@cl.header_auth_callback
def header_auth_callback(headers: dict) -> Optional[cl.User]:
    cookie = headers.get("cookie", "")
    if "auth_cpf=" in cookie:
        # Pega a PRIMEIRA ocorrência do auth_cpf (a que o browser entende como mais específica/recente)
        cookies_list = [item.strip().split("=", 1) for item in cookie.split(";") if "=" in item]
        for k, v in cookies_list:
            if k == "auth_cpf":
                cpf = v
                print(f"[DEBUG AUTH] CPF Extraído: {mask_cpf(cpf)}")
                return cl.User(identifier=cpf)
    print(f"[DEBUG AUTH] Cookie auth_cpf não encontrado. Cookies totais: {cookie}")
    return None

@cl.on_chat_start
async def on_chat_start():
    user = cl.user_session.get("user")
    if not user:
        await cl.Message(content="Sessão inválida. Por favor, volte para a tela de Login.").send()
        return
        
    # Inicializa thread e contexto usando o identificador (CPF) salvo
    thread_id = str(uuid.uuid4())
    cl.user_session.set("thread_id", thread_id)
    cl.user_session.set("cpf", user.identifier)
    
    # Envia uma mensagem de espera visualmente amigável
    msg = cl.Message(content=f"👋 Olá! Estou organizando seus dados financeiros para começar o atendimento. Só um instante... ⏳")
    await msg.send()
    
    # Prompt inicial oculto para forçar o agente a buscar o CPF e se apresentar
    initial_prompt = """O usuário acabou de abrir o chat. 
    Aja imediatamente: Chame a ferramenta `obter_roteiro_atendimento` usando o CPF do cliente.
    Siga rigorosamente os passos que ela te devolver para gerar a sua primeira mensagem de boas-vindas."""
    
    config = {"configurable": {"thread_id": thread_id}}
    
    final_response = "Erro ao inicializar o agente."
    
    # Inicializa o agente assíncrono (carrega as tools do MCP)
    agent_app = await get_agent_app()
    
    # Executa o LangGraph
    async for event in agent_app.astream({"messages": [HumanMessage(content=initial_prompt)], "cpf_ativo": user.identifier}, config, stream_mode="updates"):
        for node, update in event.items():
            if node == "chatbot":
                chatbot_msg = update["messages"][-1]
                if chatbot_msg.content:
                    final_response = chatbot_msg.content
                    
                    
    # Atualiza a mensagem de espera com a saudação oficial do agente
    msg.content = final_response
    await msg.update()

@cl.on_message
async def on_message(message: cl.Message):
    cpf = cl.user_session.get("cpf")
    thread_id = cl.user_session.get("thread_id")
    
    config = {"configurable": {"thread_id": thread_id}}
    
    # 1.3 Rate Limiting
    import time
    message_history = cl.user_session.get("message_history", [])
    current_time = time.time()
    message_history = [t for t in message_history if current_time - t < 60]
    if len(message_history) >= 10:
        await cl.Message(content="⚠️ Você enviou muitas mensagens muito rápido. Por favor, aguarde um minuto antes de enviar outra.").send()
        return
    message_history.append(current_time)
    cl.user_session.set("message_history", message_history)
    
    # Processa áudio se houver
    audio_text = ""
    if message.elements:
        for element in message.elements:
            if "audio" in element.mime and element.path:
                # Transcrever o áudio com Whisper apenas se for um anexo real de arquivo
                with open(element.path, "rb") as audio_file:
                    transcription = await openai_client.audio.transcriptions.create(
                        model="whisper-1", 
                        file=(element.name or "audio.webm", audio_file)
                    )
                    audio_text = transcription.text
                break
    
    final_content = message.content
    if audio_text:
        if final_content:
            final_content += f"\n\n[Transcrição de Áudio]: {audio_text}"
        else:
            final_content = audio_text
            
    # Forçar pesquisa atualizada antes de qualquer recomendação de investimento.
    msg_lower_check = final_content.lower()
    if "invest" in msg_lower_check or "simula" in msg_lower_check or "suger" in msg_lower_check or "opções" in msg_lower_check:
        final_content += "\n\n[SISTEMA]: OBRIGATÓRIO: Para opções, comparações ou recomendações de investimento, invoque PRIMEIRO `pesquisar_investimentos_atualizados` e apresente as 5 alternativas devolvidas. É proibido responder com opções ou taxas de memória. Depois da pesquisa, invoque `simular_investimento` uma vez para CADA alternativa que possua taxa anual efetiva confirmada, usando exatamente o mesmo aporte e prazo. Não use taxa zero quando um dado estiver ausente e não invente taxa para gerar gráfico. Na resposta final, resuma valor inicial, montante final, rendimento, riscos e hipóteses; não liste cada mês, pois o gráfico já mostra a evolução. Se a pesquisa falhar, informe a indisponibilidade e NÃO substitua por sugestões estáticas. Nunca gere gráfico em Markdown; o aplicativo renderiza as séries das tools."
            
    # Prepara a mensagem visual do Chainlit
    msg = cl.Message(content="")
    await msg.send()
    
    # Processamento do LangGraph
    final_response = "Desculpe, erro ao pensar."
    investment_projection = None
    investment_research = None
    
    # Controle da visibilidade do painel direito (Dashboard)
    from state import DASHBOARD_STATES
    msg_lower = message.content.lower()
    
    # Se pedir investimentos, esconde o dashboard imediatamente para o chat ficar em tela cheia enquanto o LLM pensa
    if "invest" in msg_lower or "simula" in msg_lower or "suger" in msg_lower or "opções" in msg_lower:
        DASHBOARD_STATES[cpf] = False
        
    # (Abertura do fluxo de caixa foi movida para o final do código para sincronizar com a mensagem)
        
    agent_app = await get_agent_app()
    
    async def processar_agente():
        nonlocal final_response, investment_projection, investment_research

        async for event in agent_app.astream({"messages": [HumanMessage(content=final_content)], "cpf_ativo": cpf}, config, stream_mode="updates"):
            for node, update in event.items():
                if node == "chatbot":
                    chatbot_msg = update["messages"][-1]
                    if hasattr(chatbot_msg, "content") and chatbot_msg.content:
                        final_response = chatbot_msg.content

                if node == "tools":
                    for tool_msg in update.get("messages", []):
                        name = getattr(tool_msg, "name", tool_msg.get("name", "")) if isinstance(tool_msg, dict) else getattr(tool_msg, "name", "")

                        if name:
                            try:
                                from state import DASHBOARD_STATES
                                if "simular" in name.lower() or "sugerir" in name.lower():
                                    DASHBOARD_STATES[cpf] = False
                                elif "transa" in name.lower() or "fluxo" in name.lower() or "goal" in name.lower() or "client" in name.lower():
                                    DASHBOARD_STATES[cpf] = True
                            except Exception as e:
                                print(f"[Erro State] {e}")

                        payload = extrair_payload_tool(tool_msg)
                        if name and "pesquisar_investimentos" in name.lower() and payload:
                            investment_research = payload

                        projection = extrair_projecao_investimento(tool_msg)
                        if projection:
                            investment_projection = combinar_projecoes_investimento(
                                investment_projection,
                                projection,
                            )

    is_investment_request = any(
        term in msg_lower for term in ("invest", "simula", "suger", "opções")
    )
    if is_investment_request:
        async with cl.Step(name="Recolhendo informações atualizadas", type="tool") as research_step:
            research_step.output = "Consultando o guia financeiro e fontes institucionais..."
            await processar_agente()
            research_step.output = "Informações reunidas e projeções calculadas."
    else:
        await processar_agente()
                                
    # 1.4 Output Guardrails
    final_response = verificar_output_guardrails(final_response)
    if is_investment_request:
        final_response = remover_detalhamento_mensal(final_response)

    # Data e fontes são anexadas pela aplicação para não depender da formatação do LLM.
    if investment_research and investment_research.get("status") == "ok":
        consulted_at = investment_research.get("consulted_at", "não informada")
        appendix = f"\n\n**Consulta atualizada:** {consulted_at}"
        final_response += appendix

    # ================= SINCRONIZAÇÃO DE UI =================
    # Só abre o dashboard DEPOIS que o LLM terminar de pensar e devolver a resposta final.
    # O controle agora é 100% feito interceptando as tools que a IA escolheu usar.
    
    # Atualiza a interface com a resposta em texto usando efeito de digitação (Streaming Simulado)
    import asyncio
    chunk_size = 4
    for i in range(0, len(final_response), chunk_size):
        chunk = final_response[i:i+chunk_size]
        await msg.stream_token(chunk)
        await asyncio.sleep(0.01) # velocidade rápida de digitação
        
    msg.content = final_response # Garante que o texto final completo esteja salvo na variável
    
    # Prepara elementos visuais (grafico e tts)
    elements_to_show = []

    if investment_projection:
        elements_to_show.append(
            cl.Plotly(
                name="Projeção dos investimentos",
                figure=criar_grafico_investimentos(investment_projection),
                display="inline",
                size="large",
            )
        )

    if investment_research and investment_research.get("status") == "ok":
        sources = investment_research.get("sources", [])[:10]
        if sources:
            elements_to_show.append(
                cl.CustomElement(
                    name="SourcesPopover",
                    props={"sources": sources},
                    display="inline",
                )
            )
    
    # Gera o Áudio da Resposta (TTS) APENAS se o usuário enviou áudio original
    if audio_text:
        try:
            # Pega no máximo os primeiros 2000 caracteres para evitar travar a API da OpenAI
            tts_input = final_response[:2000]
            tts_response = await openai_client.audio.speech.create(
                model="tts-1",
                voice="nova", # Voz amigável
                input=tts_input
            )
            # Usa .read() para garantir o download completo dos bytes do áudio antes de montar o elemento
            tts_el = cl.Audio(name="Áudio do Agente", content=tts_response.read(), display="inline", mime="audio/mp3")
            elements_to_show.append(tts_el)
        except Exception as e:
            print(f"[Erro TTS] Não foi possível gerar áudio: {e}")

    msg.elements = elements_to_show
    await msg.update()

# Hook para ativar o ícone do microfone nativo e capturar áudio gravado
@cl.on_audio_start
async def on_audio_start():
    # Inicializa o buffer na sessão
    cl.user_session.set("audio_buffer", bytearray())
    return True

@cl.on_audio_chunk
async def on_audio_chunk(chunk: cl.InputAudioChunk):
    buffer = cl.user_session.get("audio_buffer")
    if buffer is not None:
        buffer.extend(chunk.data)

@cl.on_audio_end
async def on_audio_end():
    buffer = cl.user_session.get("audio_buffer")
    if not buffer:
        return
        
    import io
    import wave
    
    # Chainlit manda PCM puro (Raw). A OpenAI precisa de um container válido (WAV)
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wav_file:
        wav_file.setnchannels(1) # Mono
        wav_file.setsampwidth(2) # 16-bit (2 bytes)
        wav_file.setframerate(24000) # Chainlit default sample rate
        wav_file.writeframes(buffer)
    
    wav_io.seek(0)
    wav_io.name = "audio.wav"
    
    # Mandar a UI mostrar que está processando
    processing_msg = cl.Message(content="🎙️ *Transcrevendo áudio...*")
    await processing_msg.send()
    
    # Transcreve o áudio gravado
    transcription = await openai_client.audio.transcriptions.create(
        model="whisper-1", 
        file=wav_io
    )
    
    # Remove a mensagem temporária de processamento
    await processing_msg.remove()
        
    # Reutiliza a lógica de mensagem criando um cl.Message visual na tela para o usuário!
    wav_io.seek(0)
    audio_el = cl.Audio(name="Seu Áudio", content=wav_io.read(), display="inline", mime="audio/wav")
    user_msg = cl.Message(author="Você", content=transcription.text, elements=[audio_el])
    await user_msg.send()
    
    # Passa o áudio transcrito como texto normal pro Agente
    await on_message(user_msg)
