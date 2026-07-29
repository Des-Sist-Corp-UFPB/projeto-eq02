from fastapi import FastAPI, HTTPException, Response, Request, WebSocket
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from tools.db import execute_query, execute_insert
from chainlit.utils import mount_chainlit
from datetime import datetime, timezone
import os
from state import DASHBOARD_STATES
from opentelemetry import trace

tracer = trace.get_tracer("api_server")

app = FastAPI(
    title="FinancIA's API",
    description="API para o sistema do Assistente Financeiro Inteligente.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.exceptions import RequestValidationError
import logging

logger = logging.getLogger(__name__)

# Tratamento Global de Exceções Genéricas (500)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Erro global não tratado", exc_info=exc, extra={"rota": request.url.path, "metodo": request.method})
    return JSONResponse(
        status_code=500,
        content={"detail": "Ocorreu um erro interno no servidor.", "error": str(exc)},
    )

# Tratamento Global de Erros de Validação (422)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": "Erro de validação nos dados fornecidos.", "errors": exc.errors()},
    )

# Monta a pasta static para servir os HTMLs de Login
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
def startup_event():
    print("--- API INICIADA COM SUCESSO ---", flush=True)

class TransactionInput(BaseModel):
    category: str
    amount: float
    description: str
    status: str
    due_date: Optional[str] = None
    paid_date: Optional[str] = None

class LoginRequest(BaseModel):
    cpf: str
    password: str

class RegisterRequest(BaseModel):
    nome: str
    cpf: str
    email: str
    password: str

class DashboardStateRequest(BaseModel):
    cpf: str
    state: bool

@app.get("/", tags=["Frontend"], summary="Redireciona para o login")
def root():
    """Redireciona o usuário para a página estática de login."""
    return RedirectResponse(url="/static/acesso-v2.html")

@app.get("/hibrido", tags=["Frontend"], summary="Página Principal")
def get_hibrido():
    """Redireciona para a interface híbrida (Chat + Dashboard)."""
    return RedirectResponse(url="/static/hibrido-v2.html")

@app.get("/dashboard", tags=["Frontend"], summary="Dashboard Isolado")
def get_dashboard():
    """Redireciona para a interface apenas do dashboard."""
    return RedirectResponse(url="/static/dashboard_only.html")

@app.get("/api/dashboard_data", tags=["Dashboard"], summary="Obter dados financeiros", description="Retorna os dados consolidados do fluxo de caixa e metas do usuário autenticado para alimentar os gráficos.")
def dashboard_data(request: Request):
    """Lê o cookie de sessão e consulta as finanças do usuário no banco."""
    cpf = request.cookies.get("auth_cpf")
    if not cpf:
        raise HTTPException(status_code=401, detail="Não autenticado")
    
    # Lê o estado de visibilidade da memória
    state_obj = DASHBOARD_STATES.get(cpf, {"view": "fluxo_caixa"})
    show_dashboard = False if state_obj is False else True
    
    view_ativa = "fluxo_caixa"
    sim_data = {}
    tool_name = ""
    if isinstance(state_obj, dict):
        view_ativa = state_obj.get("view", "fluxo_caixa")
        sim_data = state_obj.get("sim_data", {})
        tool_name = state_obj.get("tool_name", "")
    
    # O api_server agora é puramente um repassador de dados. Toda a matemática financeira mora na Tool.
    from tools.advisor import analisar_fluxo_caixa
    dados_fluxo = analisar_fluxo_caixa(cpf)
    
    if "error" in dados_fluxo:
        raise HTTPException(status_code=404, detail=dados_fluxo["error"])
        
    categorias_formatadas = [{"categoria": k, "total": v} for k, v in dados_fluxo["gastos_por_categoria"].items()]
    
    return {
        "show_dashboard": show_dashboard,
        "view": view_ativa,
        "tool_name": tool_name,
        "sim_data": sim_data,
        "renda": dados_fluxo["renda_mensal"],
        "total_gasto": dados_fluxo["total_gasto_mes_atual"],
        "saldo_livre": dados_fluxo.get("saldo_livre_projetado", 0),
        "categorias": categorias_formatadas,
        "resumo_fluxo": {
            "Gastos Efetuados": dados_fluxo.get("total_gasto_mes_atual", 0),
            "Gastos Pendentes": dados_fluxo.get("total_contas_pendentes", 0),
            "Saldo Livre": dados_fluxo.get("saldo_livre_projetado", 0)
        }
    }


@app.get("/bug", tags=["Health"], summary="Gerar Erro para Logs", description="Endpoint criado para demonstrar a coleta de erros estruturados no OpenTelemetry (Loki).")
def provoke_bug():
    """Lança um erro proposital."""
    raise ValueError("Erro intencional provocado para o exercício de Logs no Loki.")

@app.get("/ping", tags=["Health"], summary="Verificação de Saúde (Simples)", response_description="Retorna status OK e a hora atual")
async def ping():
    """Endpoint de health check usado por sistemas de monitoramento."""
    return {
        "status": "ok",
        "service": "eq02",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    }

@app.get("/health", tags=["Health"], summary="Verificação de Saúde Detalhada")
async def health():
    """Endpoint de saúde para validação do CI/CD bot."""
    return {
        "ok": True,
        "service": "eq02",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    }

@app.websocket("/ping")
async def ping_ws(websocket: WebSocket):
    """Healthcheck via WebSockets."""
    await websocket.accept()
    await websocket.send_json({"status": "ok"})
    await websocket.close()


@app.post("/login", tags=["Autenticação"], summary="Autenticar usuário", response_description="Seta os cookies de autenticação e retorna sucesso")
def login(req: LoginRequest, response: Response):
    """Recebe CPF e E-mail, valida no banco e estabelece a sessão do usuário definindo um cookie 'auth_cpf'."""
    with tracer.start_as_current_span("processar-login") as span:
        span.set_attribute("usuario.cpf", req.cpf)
        
        # Agora buscamos o hash da senha também
        clients = execute_query("SELECT cpf, password_hash FROM clients WHERE cpf = %s", (req.cpf,))
        if not clients:
            from tools.audit import log_action
            log_action("LOGIN_FAILED", req.cpf, {"reason": "User not found"})
            span.set_attribute("login.sucesso", False)
            raise HTTPException(status_code=401, detail="CPF ou Senha inválidos.")
        
        user_record = clients[0]
        stored_hash = user_record.get('password_hash')
        
        from tools.security import verify_password, create_access_token
        
        # Valida se o hash confere com a senha digitada
        if not stored_hash or not verify_password(req.password, stored_hash):
            from tools.audit import log_action
            log_action("LOGIN_FAILED", req.cpf, {"reason": "Invalid password"})
            span.set_attribute("login.sucesso", False)
            raise HTTPException(status_code=401, detail="CPF ou Senha inválidos.")
            
        span.set_attribute("login.sucesso", True)
    
    # Reseta a visibilidade do dashboard no login
    DASHBOARD_STATES[req.cpf] = False
    # Gera o token JWT
    access_token = create_access_token(data={"sub": req.cpf})
        
    # Prepara o JSON
    json_resp = JSONResponse(content={"message": "Login efetuado com sucesso!", "cpf": req.cpf})

    # IMPORTANTE: Forçar a exclusão dos cookies de sessão do Chainlit (que são HttpOnly e travam a sessão)
    json_resp.delete_cookie("access_token", path="/")
    json_resp.delete_cookie("access_token", path="/chat")
    json_resp.delete_cookie("session_id", path="/")
    json_resp.delete_cookie("session_id", path="/chat")

    # Seta o cookie com o JWT para validação forte
    json_resp.set_cookie(key="auth_token", value=access_token, httponly=True, path="/")
    # Seta o cookie do auth_cpf para a interface do frontend continuar funcionando
    json_resp.set_cookie(key="auth_cpf", value=req.cpf, httponly=False, path="/")
    json_resp.content = '{"message": "Login efetuado com sucesso!", "cpf": "' + req.cpf + '", "redirect": "/hibrido"}'
    
    from tools.audit import log_action
    log_action("LOGIN_SUCCESS", req.cpf)
    
    return json_resp

@app.post("/register", tags=["Autenticação"], summary="Registrar novo usuário", response_description="Retorna os dados do cliente criado")
def register(req: RegisterRequest):
    """Cria uma nova conta para o cliente caso o CPF ou E-mail não existam."""
    existing = execute_query("SELECT id FROM clients WHERE cpf = %s OR email = %s", (req.cpf, req.email))
    if existing:
        raise HTTPException(status_code=400, detail="CPF ou E-mail já cadastrados.")
        
    from tools.security import hash_password
    hashed_pw = hash_password(req.password)
        
    sql = """INSERT INTO clients (nome, cpf, email, password_hash, renda_total) 
             VALUES (%s, %s, %s, %s, %s) RETURNING id, nome, cpf, email"""
    new_client = execute_insert(sql, (req.nome, req.cpf, req.email, hashed_pw, 0.00))
    if not new_client:
        raise HTTPException(status_code=500, detail="Erro ao criar cliente.")
        
    from tools.audit import log_action
    log_action("REGISTER", req.cpf, {"email": req.email, "nome": req.nome})
    
    return {"success": True, "client": new_client[0]}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")

# Monta o App do Chainlit na rota /chat
mount_chainlit(app=app, target="chat_app.py", path="/chat")

import logging

class FilterUpgrade(logging.Filter):
    def filter(self, record):
        return "Unsupported upgrade request" not in record.getMessage()

# O Uvicorn imprime esse warning no logger 'uvicorn.error'.
# Injetamos nosso filtro diretamente no logger para silenciá-lo de vez.
logging.getLogger("uvicorn.error").addFilter(FilterUpgrade())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, ws="websockets")
