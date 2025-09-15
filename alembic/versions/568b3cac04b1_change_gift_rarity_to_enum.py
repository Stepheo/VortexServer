"""change_gift_rarity_to_enum

Revision ID: 568b3cac04b1
Revises: 6073246de6f3 
Create Date: 2025-09-13 22:20:07.597541
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '568b3cac04b1'
down_revision = '6073246de6f3'
branch_labels = None
depends_on = None

def upgrade():
    # Создаём ENUM тип (PostgreSQL). Если существует — пропускаем.
    gift_rarity = postgresql.ENUM('rare', 'legendary', 'ultra', name='gift_rarity')
    bind = op.get_bind()
    gift_rarity.create(bind, checkfirst=True)

    # Добавляем новую колонку с ENUM типом (временное имя)
    op.add_column(
        'gifts',
        sa.Column(
            'rarity_color_new',
            sa.Enum('rare', 'legendary', 'ultra', name='gift_rarity'),
            nullable=False,
            server_default='rare'
        )
    )

    # Перенос данных: старые значения (например '#000') мапим в 'rare'. Если вдруг уже сохранены enum строки — сохраняем их.
    op.execute(
        """
        UPDATE gifts
        SET rarity_color_new = CASE
            WHEN rarity_color IN ('rare','legendary','ultra') THEN rarity_color::gift_rarity
            ELSE 'rare'::gift_rarity
        END
        """
    )

    # Удаляем default чтобы не навязывать его на уровне схемы (оставим приложение управлять)
    op.alter_column('gifts', 'rarity_color_new', server_default=None)

    # Удаляем старую колонку и переименовываем новую
    op.drop_column('gifts', 'rarity_color')
    op.alter_column('gifts', 'rarity_color_new', new_column_name='rarity_color')

def downgrade():
    bind = op.get_bind()
    # Возвращаем строковый столбец
    op.add_column('gifts', sa.Column('rarity_color_old', sa.VARCHAR(length=20), nullable=False, server_default='#000'))
    op.execute(
        """
        UPDATE gifts
        SET rarity_color_old = CASE rarity_color
            WHEN 'legendary' THEN '#ffd700'
            WHEN 'ultra' THEN '#ff00ff'
            ELSE '#000'
        END
        """
    )
    op.alter_column('gifts', 'rarity_color_old', server_default=None)
    op.drop_column('gifts', 'rarity_color')
    op.alter_column('gifts', 'rarity_color_old', new_column_name='rarity_color')
    # Удаляем ENUM тип
    gift_rarity = postgresql.ENUM('rare', 'legendary', 'ultra', name='gift_rarity')
    gift_rarity.drop(bind, checkfirst=True)
