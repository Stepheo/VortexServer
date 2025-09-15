"""Add price column to gifts

Revision ID: 20250914_0002
Revises: 568b3cac04b1
Create Date: 2025-09-14
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250914_0002'
down_revision = '568b3cac04b1'
branch_labels = None
depends_on = None


def upgrade():
    # Add price with temporary server default 0 for existing rows
    op.add_column('gifts', sa.Column('price', sa.Numeric(10, 2), nullable=False, server_default='0'))
    # Remove server default to let application logic control future values
    op.alter_column('gifts', 'price', server_default=None)


def downgrade():
    op.drop_column('gifts', 'price')
