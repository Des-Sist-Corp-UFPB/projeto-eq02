-- Habilita a extensão pgvector para trabalhar com embeddings na busca semântica
CREATE EXTENSION IF NOT EXISTS vector;

-- Tabela de Clientes (Multi-tenancy por CPF)
CREATE TABLE IF NOT EXISTS clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cpf VARCHAR(11) UNIQUE NOT NULL,
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    renda_total NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Tabela de Transações/Gastos
CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    amount NUMERIC(10, 2) NOT NULL,
    installments INT DEFAULT 1,
    category VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    transaction_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'paid', -- 'paid' (pago/gasto) ou 'pending' (conta a pagar)
    is_recurring BOOLEAN DEFAULT FALSE,
    embedding vector(1536), -- 1536 é o tamanho padrão para embeddings da OpenAI (text-embedding-3-small)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Garantir que as colunas existam caso a tabela já tenha sido criada antes
ALTER TABLE transactions ADD COLUMN status VARCHAR(20) DEFAULT 'paid';
ALTER TABLE transactions ADD COLUMN is_recurring BOOLEAN DEFAULT FALSE;

-- Tabela de Metas Mensais
CREATE TABLE IF NOT EXISTS goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    category VARCHAR(100) NOT NULL,
    limit_amount NUMERIC(10, 2) NOT NULL,
    month_year DATE NOT NULL, -- Normalmente será inserido o 1º dia do mês referente
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Tabela de Memória de Longo Prazo do Usuário
CREATE TABLE IF NOT EXISTS user_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    fact TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Segurança de Row Level Security (Opcional por enquanto, mas boa prática no Supabase)
-- ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE goals ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE user_memory ENABLE ROW LEVEL SECURITY;

-- --------------------------------------------------------
-- INSERÇÃO DE DADOS DE TESTE (MOCK)
-- --------------------------------------------------------

INSERT INTO clients (cpf, nome, email, renda_total) VALUES
('00011122233', 'João Heslin', 'joaoheslin1@gmail.com', 3500.00),
('44455566677', 'Rita de Cássia', 'ritacassia2@gmail.com', 2000.00)
ON CONFLICT (cpf) DO NOTHING;

-- Mock Data para transações (contas pagas e pendentes do João)
INSERT INTO transactions (client_id, amount, category, description, transaction_date, status, is_recurring)
SELECT id, 150.00, 'Moradia', 'Conta de Luz', (CURRENT_DATE + INTERVAL '5 days'), 'pending', true
FROM clients WHERE cpf = '00011122233'
LIMIT 1;

INSERT INTO transactions (client_id, amount, category, description, transaction_date, status, is_recurring)
SELECT id, 60.00, 'Assinatura', 'Netflix', CURRENT_DATE, 'paid', true
FROM clients WHERE cpf = '00011122233'
LIMIT 1;