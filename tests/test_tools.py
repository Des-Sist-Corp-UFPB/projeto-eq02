from tools.security import mask_cpf, verify_password, hash_password
from tools.transactions import categorizar_transacao

def test_mask_cpf():
    """Testa se a função mask_cpf aplica corretamente a máscara."""
    cpf_puro = "12345678901"
    mascarado = mask_cpf(cpf_puro)
    assert mascarado == "***.456.789-**"

def test_mask_cpf_tamanho_incorreto():
    """Testa se a função lida graciosamente com CPFs inválidos."""
    assert mask_cpf("123") == "***.***.***-**"
    assert mask_cpf(None) == "***.***.***-**"

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


def test_categorizacao_financeira_especifica():
    assert categorizar_transacao("Compras", "Feira do mês") == "Alimentação"
    assert categorizar_transacao("Compras", "Assinaturas de streaming") == "Lazer"
    assert categorizar_transacao("Compras", "Mouse para substituir o quebrado") == "Tecnologia"
    assert categorizar_transacao("Compras", "Conserto do celular") == "Manutenção"
