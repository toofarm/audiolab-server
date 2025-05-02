"""Add tracks table

Revision ID: d3ad39f4f2c1
Revises: 3fedb9934808
Create Date: 2025-04-30 23:18:43.761734

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3ad39f4f2c1'
down_revision: Union[str, None] = '3fedb9934808'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
