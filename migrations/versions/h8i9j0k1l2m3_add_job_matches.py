"""add job_matches table

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2026-06-28 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'h8i9j0k1l2m3'
down_revision = 'g7h8i9j0k1l2'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'job_matches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('company', sa.String(), nullable=False),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('job_url', sa.String(), nullable=False),
        sa.Column('date_posted', sa.String(), nullable=True),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_job_matches_user_id', 'job_matches', ['user_id'], unique=False
    )


def downgrade():
    op.drop_index('ix_job_matches_user_id', table_name='job_matches')
    op.drop_table('job_matches')