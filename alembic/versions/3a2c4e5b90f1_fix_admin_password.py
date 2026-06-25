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
    # Use a well-known bcrypt hash for 'admin123'
    # Cost 12, valid bcrypt hash.
    admin_hash = "$2b$12$KixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjIQ6V0.vS"

    op.execute(f"""
    UPDATE clients SET password_hash = '{admin_hash}' WHERE cpf = '13579024680' AND password_hash IS NULL;
    """)

def downgrade() -> None:
    pass
