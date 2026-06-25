"""seed_data

Revision ID: e1b7dbf1a9bf
Revises: d0a6caf0f8af
Create Date: 2026-06-25 20:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1b7dbf1a9bf'
down_revision: Union[str, Sequence[str], None] = 'd0a6caf0f8af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from tools.security import hash_password
    admin_hash = hash_password("admin123")

    op.execute(f"""
    INSERT INTO clients (cpf, nome, email, password_hash, renda_total) VALUES
    ('10203040506', 'admin', 'admin@admin.com', '{admin_hash}', 2000.00)
    ON CONFLICT (cpf) DO UPDATE SET password_hash = EXCLUDED.password_hash WHERE clients.password_hash IS NULL;

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
    WHERE c.cpf = '10203040506' 
      AND NOT EXISTS (SELECT 1 FROM transactions t WHERE t.client_id = c.id);

    INSERT INTO goals (client_id, category, limit_amount, month_year)
    SELECT c.id, v.category, v.limit_amount, date_trunc('month', current_date)::date
    FROM clients c
    CROSS JOIN (
        VALUES 
            ('Alimentação', 600.00),
            ('Lazer', 150.00)
    ) AS v(category, limit_amount)
    WHERE c.cpf = '10203040506'
      AND NOT EXISTS (SELECT 1 FROM goals g WHERE g.client_id = c.id);
    """)

def downgrade() -> None:
    op.execute("""
    DELETE FROM transactions WHERE client_id IN (SELECT id FROM clients WHERE cpf = '10203040506');
    DELETE FROM goals WHERE client_id IN (SELECT id FROM clients WHERE cpf = '10203040506');
    DELETE FROM clients WHERE cpf = '10203040506';
    """)
