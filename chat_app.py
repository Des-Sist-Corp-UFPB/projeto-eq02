import chainlit as cl
from typing import Optional
from agent import get_agent_app
from langchain_core.messages import HumanMessage
import uuid
import os
from openai import AsyncOpenAI

openai_client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

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
                print(f"[DEBUG AUTH] Cookies Recebidos: {cookies_list}")
                print(f"[DEBUG AUTH] CPF Extraído: {cpf}")
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
    
    # Envia uma mensagem de espera mostrando o CPF para debug
    msg = cl.Message(content=f"Aguarde, conectando ao FinancIA's e buscando seus dados (CPF Logado: {user.identifier})...")
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
            
    # Prepara a mensagem visual do Chainlit
    msg = cl.Message(content="")
    await msg.send()
    
    # Processamento do LangGraph
    final_response = "Desculpe, erro ao pensar."
    investment_chart = None
    
    agent_app = await get_agent_app()
    
    # Executamos o stream e capturamos a ultima mensagem gerada pelo agente
    async for event in agent_app.astream({"messages": [HumanMessage(content=final_content)], "cpf_ativo": cpf}, config, stream_mode="updates"):
        for node, update in event.items():
            if node == "chatbot":
                chatbot_msg = update["messages"][-1]
                if hasattr(chatbot_msg, "content") and chatbot_msg.content:
                    final_response = chatbot_msg.content
                    
                # Intercepta se o LLM chamou ferramentas
                if hasattr(chatbot_msg, "tool_calls") and chatbot_msg.tool_calls:
                    pass # Deixamos a interceptação real para o nó 'tools' onde o retorno chega
                        
            if node == "tools":
                tool_msg = update["messages"][-1]
                name = getattr(tool_msg, "name", "")
                if name:
                    try:
                        from state import DASHBOARD_STATES
                        if name in ["simular_investimento", "sugerir_investimentos"]:
                            import json
                            # O conteúdo retornado pela tool do MCP é uma string
                            data = json.loads(tool_msg.content)
                            # Se veio como string JSON serializada duas vezes, fazemos fallback
                            if isinstance(data, str):
                                data = json.loads(data)
                                
                            if isinstance(data, dict) and "dashboard_data" in data:
                                DASHBOARD_STATES[cpf] = {
                                    "view": "investimentos",
                                    "sim_data": data["dashboard_data"],
                                    "tool_name": name
                                }
                        else:
                            # Mantem a view atual ou reseta para fluxo_caixa
                            atual = DASHBOARD_STATES.get(cpf)
                            if not isinstance(atual, dict):
                                DASHBOARD_STATES[cpf] = {"view": "fluxo_caixa"}
                            else:
                                atual["view"] = "fluxo_caixa"
                                DASHBOARD_STATES[cpf] = atual
                    except Exception as e:
                        print(f"[Erro State] {e}")

                    # Gera gráfico interativo para simulação usando os dados VINDOS DA TOOL
                    if name in ["simular_investimento", "sugerir_investimentos"] and 'data' in locals() and isinstance(data, dict) and "dashboard_data" in data:
                        try:
                            import plotly.graph_objects as go
                            sim_data = data["dashboard_data"]
                            
                            fig = go.Figure()
                            
                            if sim_data.get("chart_type") == "bar_comparison":
                                # Gráfico de Barras
                                fig.add_trace(go.Bar(x=sim_data["labels"], y=sim_data["valores"], marker_color='#38bdf8', name='Projeção Final'))
                                fig.update_layout(title=sim_data["titulo"], xaxis_title='Sugestões', yaxis_title='Montante Final (R$)', template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#94a3b8'))
                            else:
                                # Gráfico de Linhas (Simular Investimento Clássico)
                                eixo_x = sim_data["meses"]
                                evolucao = sim_data["montante"]
                                investido = sim_data["investido"]
                                fig.add_trace(go.Scatter(x=eixo_x, y=evolucao, mode='lines', name='Com Juros Compostos', line=dict(color='#38bdf8', width=3)))
                                fig.add_trace(go.Scatter(x=eixo_x, y=investido, mode='lines', name='Total Investido', line=dict(color='#f472b6', width=2, dash='dash')))
                                fig.update_layout(title='Projeção de Investimento', xaxis_title='Meses', yaxis_title='Valor Acumulado (R$)', template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#94a3b8'))
                            
                            investment_chart = cl.Plotly(name="Simulação Interativa", figure=fig, display="inline")
                        except Exception as e:
                            print(f"[Erro Plotly] {e}")
    # Atualiza a interface com a resposta em texto
    msg.content = final_response
    
    # Prepara elementos visuais (grafico e tts)
    elements_to_show = []
    if investment_chart:
        elements_to_show.append(investment_chart)
    
    # Gera o Áudio da Resposta (TTS)
    try:
        # Pega no máximo os primeiros 4000 caracteres para evitar limite da API da OpenAI
        tts_input = final_response[:4000]
        tts_response = await openai_client.audio.speech.create(
            model="tts-1",
            voice="nova", # Voz amigável
            input=tts_input
        )
        # O retorno é um HttpxBinaryResponseContent, podemos extrair os bytes com .content
        tts_el = cl.Audio(name="Áudio do Agente", content=tts_response.content, display="inline", mime="audio/mp3")
        elements_to_show.append(tts_el)
    except Exception as e:
        print(f"[Erro TTS] {e}")

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