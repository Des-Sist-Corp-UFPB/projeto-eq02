"""fix_admin_password

Revision ID: 3a2c4e5b90f1
Revises: e1b7dbf1a9bf
Create Date: 2026-06-25 20:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3a2c4e5b90f1'
down_revision: Union[str, Sequence[str], None] = 'e1b7dbf1a9bf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Como o script roda dentro do container, passlib está disponível!
    from tools.security import hash_password
    admin_hash = hash_password("admin123")

    op.execute(f"""
    UPDATE clients SET password_hash = '{admin_hash}' WHERE cpf = '13579024680';
    """)

def downgrade() -> None:
    pass
