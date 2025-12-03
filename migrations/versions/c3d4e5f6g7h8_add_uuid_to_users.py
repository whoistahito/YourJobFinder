"""add uuid to users

Revision ID: c3d4e5f6g7h8
Revises: 912215e24801
Create Date: 2025-12-03 12:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
import uuid

# revision identifiers, used by Alembic.
revision = 'c3d4e5f6g7h8'
down_revision = '912215e24801'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Alter users table to add UUID
    # Add id column
    op.add_column('users', sa.Column('id', sa.String(length=36), nullable=True))
    
    # Populate id for existing rows
    connection = op.get_bind()
    users = connection.execute(sa.text("SELECT email, position, location FROM users")).fetchall()
    for u in users:
        connection.execute(
            sa.text("UPDATE users SET id = :id WHERE email = :email AND position = :position AND location = :location"),
            {"id": str(uuid.uuid4()), "email": u[0], "position": u[1], "location": u[2]}
        )

    # Make id not nullable
    op.alter_column('users', 'id', nullable=False)

    # Drop old PK constraint
    # Use reflection to find the name of the primary key constraint
    inspector = sa.inspect(connection)
    pk_constraint = inspector.get_pk_constraint('users')
    if pk_constraint and pk_constraint['name']:
        op.drop_constraint(pk_constraint['name'], 'users', type_='primary')
    
    # Create new PK on id
    op.create_primary_key('users_pkey', 'users', ['id'])
    
    # Create unique constraint on old PK columns to maintain uniqueness logic
    op.create_unique_constraint('_user_uc', 'users', ['email', 'position', 'location'])


def downgrade():
    op.drop_constraint('_user_uc', 'users', type_='unique')
    op.drop_constraint('users_pkey', 'users', type_='primary')
    
    op.create_primary_key('users_pkey', 'users', ['email', 'position', 'location'])
    op.drop_column('users', 'id')
