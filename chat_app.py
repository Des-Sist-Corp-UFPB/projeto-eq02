import chainlit as cl
from typing import Optional
from agent import get_agent_app
from langchain_core.messages import HumanMessage
import uuid
import os
from openai import AsyncOpenAI

openai_client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

from tools.security import mask_cpf, verificar_output_guardrails

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
            
    # Forçar a invocação da tool de investimentos para evitar respostas de memória
    msg_lower_check = final_content.lower()
    if "invest" in msg_lower_check or "simula" in msg_lower_check or "suger" in msg_lower_check or "opções" in msg_lower_check:
        final_content += "\n\n[SISTEMA]: OBRIGATÓRIO: Você DEVE invocar a ferramenta 'sugerir_investimentos' ou 'simular_investimento' agora mesmo. É ESTRITAMENTE PROIBIDO responder de memória. Após receber os dados da tool, gere a sua resposta de texto para o usuário. ATENÇÃO: NUNCA tente gerar gráficos em Markdown, desenhar imagens ou tabelas complexas. Foque APENAS no texto descritivo e direto das opções."
            
    # Prepara a mensagem visual do Chainlit
    msg = cl.Message(content="")
    await msg.send()
    
    # Processamento do LangGraph
    final_response = "Desculpe, erro ao pensar."
    
    # Controle da visibilidade do painel direito (Dashboard)
    from state import DASHBOARD_STATES
    msg_lower = message.content.lower()
    
    # Se pedir investimentos, esconde o dashboard imediatamente para o chat ficar em tela cheia enquanto o LLM pensa
    if "invest" in msg_lower or "simula" in msg_lower or "suger" in msg_lower or "opções" in msg_lower:
        DASHBOARD_STATES[cpf] = False
        
    # (Abertura do fluxo de caixa foi movida para o final do código para sincronizar com a mensagem)
        
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
                tool_names = []
                for m in update.get("messages", []):
                    tool_names.append(getattr(m, "name", m.get("name", "")) if isinstance(m, dict) else getattr(m, "name", ""))
                    
                for tool_msg in update.get("messages", []):
                    name = getattr(tool_msg, "name", tool_msg.get("name", "")) if isinstance(tool_msg, dict) else getattr(tool_msg, "name", "")
                    
                    if name:
                        try:
                            from state import DASHBOARD_STATES
                            if "simular" in name.lower() or "sugerir" in name.lower():
                                DASHBOARD_STATES[cpf] = False
                            elif "transa" in name.lower() or "fluxo" in name.lower() or "goal" in name.lower() or "client" in name.lower():
                                DASHBOARD_STATES[cpf] = True
                            # (Abertura do fluxo de caixa movida para o final para sincronizar com a IA)
                        except Exception as e:
                            print(f"[Erro State] {e}")
                                
    # 1.4 Output Guardrails
    final_response = verificar_output_guardrails(final_response)

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