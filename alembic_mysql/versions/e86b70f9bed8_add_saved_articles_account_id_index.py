"""add saved_articles account_id index

Revision ID: e86b70f9bed8
Revises: 832b942b94aa
Create Date: 2026-04-18 19:46:46.929045

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e86b70f9bed8'
down_revision: Union[str, None] = '832b942b94aa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_saved_articles_account_id",
        "saved_articles",
        ["account_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_saved_articles_account_id", table_name="saved_articles")
