"""add essay table

Revision ID: 2f6d3f4f4c8d
Revises: babdd3ec9106
Create Date: 2026-04-17 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2f6d3f4f4c8d'
down_revision = 'babdd3ec9106'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'essay',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('image_urls', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_essay_timestamp'), 'essay', ['timestamp'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_essay_timestamp'), table_name='essay')
    op.drop_table('essay')
