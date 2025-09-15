"""Add img to Gift table

Revision ID: 6073246de6f3
Revises: 20250912_0001
Create Date: 2025-09-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '6073246de6f3'
down_revision = '20250912_0001'
branch_labels = None
depends_on = None

def upgrade():
    # Add column img to gifts
    op.add_column('gifts', sa.Column('img', sa.String(length=255), nullable=True))

def downgrade():
    # Remove column img from gifts
    op.drop_column('gifts', 'img')
