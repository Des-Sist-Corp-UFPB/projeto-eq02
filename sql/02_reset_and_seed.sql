-- =========================================================================
-- SCRIPT DE RESET E POVOAMENTO COMPLETO (SEED)
-- Copie e cole este código inteiro no SQL Editor do Supabase e execute.
-- ATENÇÃO: Isso apagará todos os dados atuais e recriará do zero.
-- =========================================================================

-- 1. Apaga todas as tabelas existentes para garantir um recomeço limpo
DROP TABLE IF EXISTS user_memory CASCADE;
DROP TABLE IF EXISTS goals CASCADE;
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS clients CASCADE;

-- 2. Habilita a extensão pgvector (se já não estiver)
CREATE EXTENSION IF NOT EXISTS vector;

-- 3. Recriação da Tabela de Clientes
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cpf VARCHAR(11) UNIQUE NOT NULL,
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    renda_total NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 4. Recriação da Tabela de Transações (com a coluna installments)
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    amount NUMERIC(10, 2) NOT NULL,
    installments INT DEFAULT 1,
    category VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    transaction_date DATE NOT NULL,
    embedding vector(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 5. Recriação da Tabela de Metas Mensais
CREATE TABLE goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    category VARCHAR(100) NOT NULL,
    limit_amount NUMERIC(10, 2) NOT NULL,
    month_year DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 6. Recriação da Tabela de Memória
CREATE TABLE user_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    fact TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- =========================================================================
-- POVOAMENTO SINTÉTICO (SEED DATA)
-- =========================================================================

-- Inserindo Clientes
INSERT INTO clients (cpf, nome, email, renda_total) VALUES
('00011122233', 'João Heslin', 'joaoheslin1@gmail.com', 3500.00),
('44455566677', 'Rita de Cássia', 'ritacassia2@gmail.com', 2000.00);

-- Inserindo Transações (João)
-- O sub-select é usado para buscar o UUID correto gerado dinamicamente
INSERT INTO transactions (client_id, amount, installments, category, description, transaction_date)
SELECT id, 5000.00, 10, 'Eletrônicos', 'TV Smart 50" (10x)', (CURRENT_DATE - INTERVAL '2 months') FROM clients WHERE cpf = '00011122233'
UNION ALL
SELECT id, 3600.00, 12, 'Eletrodomésticos', 'Geladeira Brastemp (12x)', (CURRENT_DATE - INTERVAL '5 months') FROM clients WHERE cpf = '00011122233'
UNION ALL
SELECT id, 150.00, 1, 'Alimentação', 'Compra no Mercado Livre', (CURRENT_DATE - INTERVAL '2 days') FROM clients WHERE cpf = '00011122233'
UNION ALL
SELECT id, 80.00, 1, 'Lazer', 'Cinema e Pipoca', (CURRENT_DATE - INTERVAL '5 days') FROM clients WHERE cpf = '00011122233'
UNION ALL
SELECT id, 400.00, 1, 'Moradia', 'Conta de Luz', (CURRENT_DATE - INTERVAL '10 days') FROM clients WHERE cpf = '00011122233';

-- Inserindo Transações (Rita)
INSERT INTO transactions (client_id, amount, installments, category, description, transaction_date)
SELECT id, 2500.00, 5, 'Eletrônicos', 'Notebook Usado (5x)', (CURRENT_DATE - INTERVAL '1 month') FROM clients WHERE cpf = '44455566677'
UNION ALL
SELECT id, 60.00, 1, 'Transporte', 'Uber para o trabalho', (CURRENT_DATE - INTERVAL '1 day') FROM clients WHERE cpf = '44455566677'
UNION ALL
SELECT id, 200.00, 1, 'Saúde', 'Consulta Médica', (CURRENT_DATE - INTERVAL '15 days') FROM clients WHERE cpf = '44455566677';

-- Inserindo Metas (João)
-- Metas fixadas no primeiro dia do mês atual
INSERT INTO goals (client_id, category, limit_amount, month_year)
SELECT id, 'Alimentação', 800.00, date_trunc('month', CURRENT_DATE)::DATE FROM clients WHERE cpf = '00011122233'
UNION ALL
SELECT id, 'Lazer', 300.00, date_trunc('month', CURRENT_DATE)::DATE FROM clients WHERE cpf = '00011122233';

-- Inserindo Metas (Rita)
INSERT INTO goals (client_id, category, limit_amount, month_year)
SELECT id, 'Transporte', 250.00, date_trunc('month', CURRENT_DATE)::DATE FROM clients WHERE cpf = '44455566677'
UNION ALL
SELECT id, 'Eletrônicos', 600.00, date_trunc('month', CURRENT_DATE)::DATE FROM clients WHERE cpf = '44455566677';

-- Inserindo Memórias (João)
INSERT INTO user_memory (client_id, fact)
SELECT id, 'Está economizando para comprar um carro zero no final do ano.' FROM clients WHERE cpf = '00011122233'
UNION ALL
SELECT id, 'Gosta de almoçar fora aos finais de semana, mas quer reduzir esse gasto.' FROM clients WHERE cpf = '00011122233';

-- Inserindo Memórias (Rita)
INSERT INTO user_memory (client_id, fact)
SELECT id, 'Pretende fazer uma viagem internacional no próximo ano.' FROM clients WHERE cpf = '44455566677'
UNION ALL
SELECT id, 'Sempre guarda 10% da sua renda assim que o salário cai na conta.' FROM clients WHERE cpf = '44455566677';