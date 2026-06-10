from fastapi import FastAPI, HTTPException, Response, Request
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
    print("--- INICIANDO SETUP DO BANCO DE DADOS ---", flush=True)
    schema_path = os.path.join(os.path.dirname(__file__), "sql", "01_init_schema.sql")
    print(f"Caminho do script: {schema_path}", flush=True)
    if os.path.exists(schema_path):
        print("Arquivo encontrado! Rodando script...", flush=True)
        with open(schema_path, "r", encoding="utf-8") as f:
            sql_script = f.read()
        
        # Vamos dividir o script por ';' e rodar comando por comando
        # Isso evita que um erro (como CREATE EXTENSION sem permissão) aborte a criação das tabelas
        commands = sql_script.split(';')
        for cmd in commands:
            cmd = cmd.strip()
            if cmd:
                print(f"Rodando: {cmd[:50]}...", flush=True)
                execute_query(cmd, fetch=False)
        print("--- SETUP DO BANCO FINALIZADO ---", flush=True)
    else:
        print("ERRO: Arquivo sql/01_init_schema.sql NAO ENCONTRADO!", flush=True)
        print(f"Arquivos na pasta atual: {os.listdir(os.path.dirname(__file__))}", flush=True)

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

@app.get("/hibrido")
def get_hibrido():
    return RedirectResponse(url="/static/hibrido.html")

@app.get("/dashboard")
def get_dashboard():
    return RedirectResponse(url="/static/dashboard_only.html")

@app.get("/api/dashboard_data")
def dashboard_data(request: Request):
    cpf = request.cookies.get("auth_cpf")
    if not cpf:
        raise HTTPException(status_code=401, detail="Não autenticado")
    
    # Lê o estado de visibilidade
    show_dashboard = False
    state_file = os.path.join(os.path.dirname(__file__), f"state_{cpf}.json")
    if os.path.exists(state_file):
        import json
        try:
            with open(state_file, "r") as f:
                state = json.load(f)
                show_dashboard = state.get("show_dashboard", False)
        except:
            pass

    # Busca cliente
    client = execute_query("SELECT id, renda_total FROM clients WHERE cpf = %s", (cpf,), fetch=True, fetch_one=True)
    if not client:
         raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    client_id = client[0]['id']
    renda = float(client[0]['renda_total'])
    
    # Busca gastos do mês atual
    hoje = datetime.now()
    inicio_mes = hoje.replace(day=1).strftime('%Y-%m-%d')
    
    gastos = execute_query(
        "SELECT category, SUM(amount) as total FROM transactions WHERE client_id = %s AND transaction_date >= %s GROUP BY category",
        (client_id, inicio_mes)
    )
    
    total_gasto = sum([float(g['total']) for g in gastos]) if gastos else 0.0
    saldo_livre = renda - total_gasto
    
    # 50/30/20 baseado no GASTO (ou na Renda, o gráfico mostraremos o que foi gasto vs o que deveria)
    necessidades_gasto = sum([float(g['total']) for g in gastos if g['category'] in ['Moradia', 'Alimentação', 'Saúde', 'Transporte', 'Educação']])
    desejos_gasto = sum([float(g['total']) for g in gastos if g['category'] in ['Lazer', 'Roupas', 'Eletrônicos', 'Restaurante']])
    # O resto cai em outros ou investimentos
    
    return {
        "show_dashboard": show_dashboard,
        "renda": renda,
        "total_gasto": total_gasto,
        "saldo_livre": saldo_livre,
        "categorias": [{"categoria": g['category'], "total": float(g['total'])} for g in gastos],
        "regra_50_30_20": {
            "Necessidades": necessidades_gasto,
            "Desejos": desejos_gasto,
            "Futuro": total_gasto - necessidades_gasto - desejos_gasto # Simplificação para o gráfico atual
        }
    }

@app.get("/ping")
def ping():
    return {
        "status": "ok",
        "service": "eq02",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    }

@app.get("/debug_db")
def debug_db():
    try:
        # Puxa os nomes de todas as tabelas criadas pelo usuário (no schema public)
        tables_query = execute_query("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = [t["table_name"] for t in tables_query] if tables_query else []
        
        # Puxa as informações específicas de transações, se existir
        cols = execute_query("SELECT column_name FROM information_schema.columns WHERE table_name = 'transactions'")
        col_names = [c["column_name"] for c in cols] if cols else []
        
        trans = execute_query("SELECT id, description, status, transaction_date FROM transactions LIMIT 5")
        
        return {
            "todas_as_tabelas_no_banco": tables,
            "colunas_da_tabela_transactions": col_names,
            "dados_de_exemplo_transactions": trans
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/login")
def login(req: LoginRequest, response: Response):
    clients = execute_query("SELECT * FROM clients WHERE cpf = %s AND email = %s", (req.cpf, req.email))
    if not clients:
        raise HTTPException(status_code=401, detail="CPF ou E-mail inválidos.")
    
    # Reseta a visibilidade do dashboard no login
    import json
    import os
    state_file = os.path.join(os.path.dirname(__file__), f"state_{req.cpf}.json")
    with open(state_file, "w") as f:
        json.dump({"show_dashboard": False}, f)
        
    # Prepara o JSON e seta o Cookie para o Chainlit poder ler
    json_resp = JSONResponse(content={"message": "Login efetuado com sucesso!", "cpf": req.cpf})

    # IMPORTANTE: Forçar a exclusão dos cookies de sessão do Chainlit (que são HttpOnly e travam a sessão)
    json_resp.delete_cookie("access_token", path="/")
    json_resp.delete_cookie("access_token", path="/chat")
    json_resp.delete_cookie("session_id", path="/")
    json_resp.delete_cookie("session_id", path="/chat")

    json_resp.set_cookie(key="auth_cpf", value=req.cpf, httponly=False, path="/")
    json_resp.content = '{"message": "Login efetuado com sucesso!", "cpf": "' + req.cpf + '", "redirect": "/hibrido"}'
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