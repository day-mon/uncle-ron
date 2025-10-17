"""Ensure temperature and max_tokens columns exist

Revision ID: ea3c3f5c41ce
Revises: f045f57e416b
Create Date: 2025-10-16 21:31:57.993353

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ea3c3f5c41ce'
down_revision: Union[str, Sequence[str], None] = 'f045f57e416b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if columns exist and add them if they don't
    # SQLite-compatible approach using raw SQL
    connection = op.get_bind()
    
    # Check if temperature column exists
    result = connection.execute(sa.text("PRAGMA table_info(thread_settings)"))
    columns = [row[1] for row in result.fetchall()]
    
    if 'temperature' not in columns:
        op.add_column('thread_settings', sa.Column('temperature', sa.Float(), nullable=True))
    
    if 'max_tokens' not in columns:
        op.add_column('thread_settings', sa.Column('max_tokens', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # SQLite doesn't support dropping columns easily, so we'll leave them
    # In a real scenario, you'd need to recreate the table without these columns
    pass
