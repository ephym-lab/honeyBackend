"""rename image to image_cover

Revision ID: 3512465f1df5
Revises: 0556eade91df
Create Date: 2026-07-16 07:23:51.922310

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3512465f1df5'
down_revision: Union[str, None] = '0556eade91df'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename column 'image' to 'image_cover'
    op.alter_column('products', 'image', new_column_name='image_cover')

def downgrade() -> None:
    # Rename column 'image_cover' back to 'image'
    op.alter_column('products', 'image_cover', new_column_name='image')
