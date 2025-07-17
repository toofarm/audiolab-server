"""straighten_things_out

Revision ID: bf02b53772cb
Revises: 6462102c28bb, add_spotify_like_features
Create Date: 2025-07-11 22:39:18.764373

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bf02b53772cb'
down_revision: Union[str, None] = ('6462102c28bb', 'add_spotify_like_features')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
