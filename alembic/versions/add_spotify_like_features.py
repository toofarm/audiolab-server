"""add spotify like features

Revision ID: add_spotify_like_features
Revises: 1684fd3f5d83
Create Date: 2025-01-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_spotify_like_features'
down_revision: Union[str, None] = '1684fd3f5d83'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add Spotify-like audio feature columns
    op.add_column('tracks', sa.Column(
        'danceability', sa.Float(), nullable=True))
    op.add_column('tracks', sa.Column('energy', sa.Float(), nullable=True))
    op.add_column('tracks', sa.Column('valence', sa.Float(), nullable=True))
    op.add_column('tracks', sa.Column(
        'acousticness', sa.Float(), nullable=True))
    op.add_column('tracks', sa.Column(
        'instrumentalness', sa.Float(), nullable=True))
    op.add_column('tracks', sa.Column('liveness', sa.Float(), nullable=True))
    op.add_column('tracks', sa.Column(
        'speechiness', sa.Float(), nullable=True))
    op.add_column('tracks', sa.Column('loudness', sa.Float(), nullable=True))
    op.add_column('tracks', sa.Column('key', sa.String(), nullable=True))
    op.add_column('tracks', sa.Column('mode', sa.String(), nullable=True))
    op.add_column('tracks', sa.Column(
        'time_signature', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove Spotify-like audio feature columns
    op.drop_column('tracks', 'time_signature')
    op.drop_column('tracks', 'mode')
    op.drop_column('tracks', 'key')
    op.drop_column('tracks', 'loudness')
    op.drop_column('tracks', 'speechiness')
    op.drop_column('tracks', 'liveness')
    op.drop_column('tracks', 'instrumentalness')
    op.drop_column('tracks', 'acousticness')
    op.drop_column('tracks', 'valence')
    op.drop_column('tracks', 'energy')
    op.drop_column('tracks', 'danceability')
