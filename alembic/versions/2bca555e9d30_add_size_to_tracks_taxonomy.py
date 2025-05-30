"""add size to tracks taxonomy

Revision ID: 2bca555e9d30
Revises: 444acde3116b
Create Date: 2025-05-29 22:33:28.742929

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2bca555e9d30'
down_revision: Union[str, None] = '444acde3116b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tracks', sa.Column('size', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('tracks', 'size')
    # ### end Alembic commands ###
