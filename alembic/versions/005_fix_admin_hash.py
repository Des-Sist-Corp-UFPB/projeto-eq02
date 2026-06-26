"""fix_admin_hash

Revision ID: 005
Revises: 004
Create Date: 2026-06-25 20:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, Sequence[str], None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Gera um hash bcrypt válido usando o código que já corrigimos (puro bcrypt)
    from tools.security import hash_password
    admin_hash = hash_password("admin123")

    # Atualiza o hash inválido do banco para o hash recém-gerado
    op.execute(f"""
    UPDATE clients SET password_hash = '{admin_hash}' WHERE cpf = '10203040506';
    """)

def downgrade() -> None:
    pass
