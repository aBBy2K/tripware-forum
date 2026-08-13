"""add fulltext posts

Revision ID: e62bcfde9d89
Revises: cce575828963
Create Date: 2026-07-13 19:29:01.370390

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e62bcfde9d89'
down_revision: Union[str, Sequence[str], None] = 'cce575828963'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TABLE posts ADD FULLTEXT INDEX ft_posts_search(title, body)")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE posts DROP INDEX ft_posts_search")
    pass
