"""add card_likes account unique constraint

Revision ID: f84b02321df9
Revises: e86b70f9bed8
Create Date: 2026-04-18 20:00:48.958001

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'f84b02321df9'
down_revision: Union[str, None] = 'e86b70f9bed8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_card_like_account",
        "card_likes",
        ["shared_card_id", "liker_account_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_card_like_account", "card_likes", type_="unique")
