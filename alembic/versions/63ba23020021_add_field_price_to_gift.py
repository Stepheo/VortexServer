"""Add price field to gifts

Revision ID: 63ba23020021
Revises: 20250914_0002
Create Date: 2025-09-14 23:02:30.582833
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '63ba23020021'
down_revision = '20250914_0002'
branch_labels = None
depends_on = None

def upgrade():
    # Add price with temporary default for existing rows
    op.add_column(
        'gifts',
        sa.Column('price', sa.Numeric(10, 2), nullable=False, server_default='0')
    )
    # Remove default afterward
    op.alter_column('gifts', 'price', server_default=None)

def downgrade():
    op.drop_column('gifts', 'price')
