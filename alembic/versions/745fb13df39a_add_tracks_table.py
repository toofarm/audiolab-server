"""Add tracks table

Revision ID: 745fb13df39a
Revises: d3ad39f4f2c1
Create Date: 2025-04-30 23:20:27.760237

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '745fb13df39a'
down_revision: Union[str, None] = 'd3ad39f4f2c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
