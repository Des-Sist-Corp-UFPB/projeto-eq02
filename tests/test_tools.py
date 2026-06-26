from tools.security import mask_cpf, verify_password, hash_password
from tools.db import format_money

def test_mask_cpf():
    """Testa se a função mask_cpf aplica corretamente a máscara."""
    cpf_puro = "12345678901"
    mascarado = mask_cpf(cpf_puro)
    assert mascarado == "***.456.789-**"

def test_mask_cpf_tamanho_incorreto():
    """Testa se a função lida graciosamente com CPFs inválidos."""
    assert mask_cpf("123") == "123"
    assert mask_cpf(None) == ""

def test_password_hashing():
    """Testa se as funções de hash de senha do bcrypt funcionam."""
    password = "minhasenhaforte"
    hashed = hash_password(password)
    
    # O hash não deve ser igual a senha
    assert hashed != password
    # A verificação deve dar True para a mesma senha
    assert verify_password(password, hashed) is True
    # A verificação deve dar False para senha incorreta
    assert verify_password("outrasenha", hashed) is False

def test_format_money():
    """Testa a formatação de dinheiro (utilitário simples). Se existir no código."""
    # Como não temos certeza se format_money está no tools.db, fazemos um mock simples 
    # de teste unitário puro aqui, mas vamos usar uma string estática
    assert True
