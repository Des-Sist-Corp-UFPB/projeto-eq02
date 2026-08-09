"""change_admin_cpf

Revision ID: 004
Revises: 003
Create Date: 2026-06-25 20:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, Sequence[str], None] = '3a2c4e5b90f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Atualiza o CPF do Admin de 13579024680 para 10203040506
    op.execute("""
    UPDATE clients SET cpf = '10203040506' WHERE cpf = '13579024680';
    """)

def downgrade() -> None:
    op.execute("""
    UPDATE clients SET cpf = '13579024680' WHERE cpf = '10203040506';
    """)
