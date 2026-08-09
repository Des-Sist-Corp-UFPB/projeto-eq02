# pyrefly: ignore [missing-import]
import pytest
from unittest.mock import patch, MagicMock
import sys
sys.modules['chainlit.utils'] = MagicMock()

from api_server import app
from fastapi.testclient import TestClient

# Inicializa o TestClient para uso em todos os testes
@pytest.fixture
def client():
    return TestClient(app)

# Mock global para evitar conexões com o banco de dados durante os testes unitários
@pytest.fixture(autouse=True)
def mock_db_connection():
    with patch('tools.db.psycopg2.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        yield mock_connect
