import os
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

_pool = None

def get_pool():
    global _pool
    if _pool is None:
        _pool = ThreadedConnectionPool(
            1, 20,
            host=os.environ.get("DB_HOST"),
            port=os.environ.get("DB_PORT"),
            dbname=os.environ.get("DB_NAME"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD"),
            cursor_factory=RealDictCursor
        )
    return _pool

def get_db_connection():
    return get_pool().getconn()

def release_db_connection(conn):
    if _pool and conn:
        _pool.putconn(conn)

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
            result = []
            if fetch:
                if fetch_one:
                    res = cur.fetchone()
                    result = [res] if res else []
                else:
                    result = cur.fetchall()
            conn.commit()
            return result
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Erro no banco de dados: {e}")
        return []
    finally:
        if conn:
            release_db_connection(conn)

def execute_insert(sql: str, params: tuple = None):
    """
    Executa um INSERT retornando os dados recém-inseridos.
    O SQL DEVE terminar com `RETURNING *`.
    """
    return execute_query(sql, params, fetch=True, fetch_one=True)
