-- Habilita a extensão pgvector para trabalhar com embeddings na busca semântica
-- CREATE EXTENSION IF NOT EXISTS vector

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
    -- embedding vector(1536), -- 1536 é o tamanho padrão para embeddings da OpenAI (text-embedding-3-small)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Garantir que as colunas existam caso a tabela já tenha sido criada antes
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'paid';
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS is_recurring BOOLEAN DEFAULT FALSE;

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
-- ALTER TABLE clients ENABLE ROW LEVEL SECURITY
-- ALTER TABLE transactions ENABLE ROW LEVEL SECURITY
-- ALTER TABLE goals ENABLE ROW LEVEL SECURITY
-- ALTER TABLE user_memory ENABLE ROW LEVEL SECURITY

-- --------------------------------------------------------
-- Dados Iniciais (Seed)
-- --------------------------------------------------------

INSERT INTO clients (cpf, nome, email, renda_total) VALUES
('13579024680', 'admin', 'admin@admin.com', 2000.00)
ON CONFLICT (cpf) DO NOTHING;

-- Mock Data para transações (contas pagas e pendentes do Admin) e Metas
-- Só insere se o admin ainda não tiver transações (evita duplicar a cada restart do servidor)
INSERT INTO transactions (client_id, amount, installments, category, description, transaction_date, status, is_recurring)
SELECT c.id, v.amount, v.installments, v.category, v.description, v.transaction_date::date, v.status, v.is_recurring
FROM clients c
CROSS JOIN (
    VALUES 
        (150.00, 1, 'Moradia', 'Conta de Luz', current_date - interval '5 days', 'paid', true),
        (100.00, 1, 'Moradia', 'Internet', current_date - interval '4 days', 'paid', true),
        (450.00, 1, 'Alimentação', 'Compra do Mês no Mercado', current_date - interval '2 days', 'paid', false),
        (45.90, 1, 'Lazer', 'Netflix', current_date - interval '1 day', 'paid', true),
        (800.00, 1, 'Moradia', 'Aluguel', current_date + interval '5 days', 'pending', true),
        (120.00, 3, 'Compras', 'Tênis novo (Parcela 1/3)', current_date - interval '10 days', 'paid', false)
) AS v(amount, installments, category, description, transaction_date, status, is_recurring)
WHERE c.cpf = '13579024680' 
  AND NOT EXISTS (SELECT 1 FROM transactions t WHERE t.client_id = c.id);

INSERT INTO goals (client_id, category, limit_amount, month_year)
SELECT c.id, v.category, v.limit_amount, date_trunc('month', current_date)::date
FROM clients c
CROSS JOIN (
    VALUES 
        ('Alimentação', 600.00),
        ('Lazer', 150.00)
) AS v(category, limit_amount)
WHERE c.cpf = '13579024680'
  AND NOT EXISTS (SELECT 1 FROM goals g WHERE g.client_id = c.id);