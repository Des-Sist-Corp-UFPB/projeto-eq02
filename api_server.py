from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from tools.db import execute_query, execute_insert
from chainlit.utils import mount_chainlit
from datetime import datetime, timezone
import os

app = FastAPI(title="FinancIA's API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Monta a pasta static para servir os HTMLs de Login
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
def startup_event():
    # Inicializa as tabelas do banco de dados se não existirem
    schema_path = os.path.join(os.path.dirname(__file__), "sql", "01_init_schema.sql")
    if os.path.exists(schema_path):
        with open(schema_path, "r", encoding="utf-8") as f:
            sql_script = f.read()
        execute_query(sql_script, fetch=False)

class LoginRequest(BaseModel):
    cpf: str
    email: str

class RegisterRequest(BaseModel):
    nome: str
    cpf: str
    email: str

@app.get("/")
def root():
    return RedirectResponse(url="/static/login.html")

@app.get("/ping")
def ping():
    return {
        "status": "ok",
        "service": "eq02",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    }

@app.post("/login")
def login(req: LoginRequest, response: Response):
    clients = execute_query("SELECT * FROM clients WHERE cpf = %s AND email = %s", (req.cpf, req.email))
    if not clients:
        raise HTTPException(status_code=401, detail="CPF ou E-mail inválidos.")
    
    # Prepara o JSON e seta o Cookie para o Chainlit poder ler
    json_resp = JSONResponse(content={"message": "Login efetuado com sucesso!", "cpf": req.cpf})

    # IMPORTANTE: Forçar a exclusão dos cookies de sessão do Chainlit (que são HttpOnly e travam a sessão)
    json_resp.delete_cookie("access_token", path="/")
    json_resp.delete_cookie("access_token", path="/chat")
    json_resp.delete_cookie("session_id", path="/")
    json_resp.delete_cookie("session_id", path="/chat")

    json_resp.set_cookie(key="auth_cpf", value=req.cpf, httponly=False, path="/")
    return json_resp

@app.post("/register")
def register(req: RegisterRequest):
    existing = execute_query("SELECT id FROM clients WHERE cpf = %s", (req.cpf,))
    if existing:
        raise HTTPException(status_code=400, detail="CPF já cadastrado.")
        
    sql = """INSERT INTO clients (nome, cpf, email, renda_total) 
             VALUES (%s, %s, %s, %s) RETURNING *"""
    new_client = execute_insert(sql, (req.nome, req.cpf, req.email, 0.00))
    if not new_client:
        raise HTTPException(status_code=500, detail="Erro ao criar cliente.")
    return {"success": True, "client": new_client[0]}

# Monta o App do Chainlit na rota /chat
mount_chainlit(app=app, target="chat_app.py", path="/chat")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)