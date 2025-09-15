"""Initial revision: drop legacy gifts column, add case_gifts table

Revision ID: 20250912_0001
Revises: 
Create Date: 2025-09-12
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250912_0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Drop legacy column gifts if exists (PostgreSQL specific conditional)
    conn = op.get_bind()
    insp = sa.inspect(conn)
    if 'cases' in insp.get_table_names():
        cols = {c['name'] for c in insp.get_columns('cases')}
        if 'gifts' in cols:
            op.drop_column('cases', 'gifts')

    # Create association table if not exists
    if 'case_gifts' not in insp.get_table_names():
        op.create_table(
            'case_gifts',
            sa.Column('case_id', sa.BigInteger(), sa.ForeignKey('cases.id', ondelete='CASCADE'), primary_key=True),
            sa.Column('gift_id', sa.BigInteger(), sa.ForeignKey('gifts.id', ondelete='CASCADE'), primary_key=True),
        )


def downgrade():
    # Drop association table
    op.drop_table('case_gifts')
    # (Optional) Can't restore old JSON gifts column automatically without data snapshot
    # op.add_column('cases', sa.Column('gifts', sa.JSON(), nullable=True))
