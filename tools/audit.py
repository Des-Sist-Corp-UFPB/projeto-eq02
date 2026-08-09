import json
from tools.db import execute_insert

def log_action(action: str, user_cpf: str, details: dict = None):
    """
    Registra uma ação no módulo de log de auditoria.
    
    :param action: Ação realizada (ex: 'LOGIN_SUCCESS', 'REGISTER', 'LOGIN_FAILED')
    :param user_cpf: CPF do usuário que realizou/sofreu a ação
    :param details: Dicionário contendo dados extras para auditoria
    """
    details_json = json.dumps(details, default=str, ensure_ascii=False) if details else "{}"
    
    sql = """
        INSERT INTO audit_logs (action, user_cpf, details)
        VALUES (%s, %s, %s)
        RETURNING id, action, user_cpf, details, created_at;
    """
    
    try:
        execute_insert(sql, (action, user_cpf, details_json))
    except Exception as e:
        print(f"Erro ao registrar auditoria: {e}")
