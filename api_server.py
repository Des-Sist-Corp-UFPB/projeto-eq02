from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from tools.db import supabase
from chainlit.utils import mount_chainlit
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

@app.post("/login")
def login(req: LoginRequest, response: Response):
    res = supabase.table("clients").select("*").eq("cpf", req.cpf).eq("email", req.email).execute()
    if not res.data:
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
    res_cpf = supabase.table("clients").select("id").eq("cpf", req.cpf).execute()
    if res_cpf.data:
        raise HTTPException(status_code=400, detail="CPF já cadastrado.")
        
    data = {
        "nome": req.nome,
        "cpf": req.cpf,
        "email": req.email,
        "renda_total": 0.00
    }
    res = supabase.table("clients").insert(data).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Erro ao criar cliente.")
    return {"success": True, "client": res.data[0]}

# Monta o App do Chainlit na rota /chat
mount_chainlit(app=app, target="chat_app.py", path="/chat")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)