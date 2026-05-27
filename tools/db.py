import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST"),
        port=os.environ.get("DB_PORT"),
        dbname=os.environ.get("DB_NAME"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        cursor_factory=RealDictCursor
    )

def execute_query(sql: str, params: tuple = None, fetch: bool = True, fetch_one: bool = False):
    """
    Executa uma consulta SQL de forma segura.
    Se fetch=True, retorna os resultados. Se fetch_one=True, retorna apenas a primeira linha.
    Retorna uma lista de dicionários (ou um dicionário único) com os dados.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(sql, params)
            if fetch:
                if fetch_one:
                    res = cur.fetchone()
                    return [res] if res else [] # Mantém formato de lista similar ao data do supabase
                res = cur.fetchall()
                return res
            conn.commit()
            return []
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Erro no banco de dados: {e}")
        return []
    finally:
        if conn:
            conn.close()

def execute_insert(sql: str, params: tuple = None):
    """
    Executa um INSERT retornando os dados recém-inseridos.
    O SQL DEVE terminar com `RETURNING *`.
    """
    return execute_query(sql, params, fetch=True, fetch_one=True)
