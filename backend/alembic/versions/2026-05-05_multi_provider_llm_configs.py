"""multi provider llm configs

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-05 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create user_llm_configs table (skip if already exists from create_all)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'user_llm_configs' not in inspector.get_table_names():
        op.create_table(
            'user_llm_configs',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('provider', sa.String(length=50), nullable=False),
            sa.Column('model', sa.String(length=100), nullable=True),
            sa.Column('api_key', sa.String(length=500), nullable=True),
            sa.Column('base_url', sa.String(length=500), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_user_llm_configs_user_id', 'user_llm_configs', ['user_id'])

    # Migrate existing data from users table (only if old columns exist)
    user_columns = {col['name'] for col in inspector.get_columns('users')}
    if 'llm_provider' in user_columns:
        users = conn.execute(sa.text(
            "SELECT id, llm_provider, llm_api_key, llm_model, llm_base_url FROM users "
            "WHERE llm_provider IS NOT NULL AND llm_api_key IS NOT NULL"
        )).fetchall()
        for user in users:
            conn.execute(sa.text(
                "INSERT INTO user_llm_configs (id, user_id, provider, model, api_key, base_url) "
                "VALUES (:id, :user_id, :provider, :model, :api_key, :base_url)"
            ), {
                "id": str(__import__('uuid').uuid4()),
                "user_id": user[0],
                "provider": user[1],
                "model": user[3],
                "api_key": user[2],
                "base_url": user[4],
            })

        # Drop old columns from users
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.drop_column('llm_base_url')
            batch_op.drop_column('llm_api_key')
            batch_op.drop_column('llm_model')
            batch_op.drop_column('llm_provider')


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    user_columns = {col['name'] for col in inspector.get_columns('users')}

    # Add old columns back (only if they don't exist)
    if 'llm_provider' not in user_columns:
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.add_column(sa.Column('llm_provider', sa.String(length=50), nullable=True))
            batch_op.add_column(sa.Column('llm_model', sa.String(length=100), nullable=True))
            batch_op.add_column(sa.Column('llm_api_key', sa.String(length=500), nullable=True))
            batch_op.add_column(sa.Column('llm_base_url', sa.String(length=500), nullable=True))

    # Migrate data back (take first config per user, if table exists)
    if 'user_llm_configs' in inspector.get_table_names():
        configs = conn.execute(sa.text(
            "SELECT user_id, provider, model, api_key, base_url FROM user_llm_configs"
        )).fetchall()
        for cfg in configs:
            conn.execute(sa.text(
                "UPDATE users SET llm_provider=:p, llm_model=:m, llm_api_key=:k, llm_base_url=:b WHERE id=:uid"
            ), {"p": cfg[1], "m": cfg[2], "k": cfg[3], "b": cfg[4], "uid": cfg[0]})

        indexes = {idx['name'] for idx in inspector.get_indexes('user_llm_configs')}
        if 'ix_user_llm_configs_user_id' in indexes:
            op.drop_index('ix_user_llm_configs_user_id', table_name='user_llm_configs')
        op.drop_table('user_llm_configs')
