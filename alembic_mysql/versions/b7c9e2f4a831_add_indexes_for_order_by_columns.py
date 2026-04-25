"""add indexes for order_by columns

Revision ID: b7c9e2f4a831
Revises: ef729a73e548
Create Date: 2026-04-25 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op

revision: str = 'b7c9e2f4a831'
down_revision: Union[str, None] = 'ef729a73e548'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index('ix_analysis_logs_analyzed_at', 'analysis_logs', ['analyzed_at'])
    op.create_index('ix_analysis_logs_symbol', 'analysis_logs', ['symbol'])
    op.create_index('ix_boards_created_at', 'boards', ['created_at'])
    op.create_index('ix_notifications_created_at', 'notifications', ['created_at'])
    op.create_index('ix_raw_articles_created_at', 'raw_articles', ['created_at'])
    op.create_index('ix_saved_articles_saved_at', 'saved_articles', ['saved_at'])
    op.create_index('ix_accounts_created_at', 'accounts', ['created_at'])
    op.create_index('ix_shared_cards_created_at', 'shared_cards', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_analysis_logs_analyzed_at', table_name='analysis_logs')
    op.drop_index('ix_analysis_logs_symbol', table_name='analysis_logs')
    op.drop_index('ix_boards_created_at', table_name='boards')
    op.drop_index('ix_notifications_created_at', table_name='notifications')
    op.drop_index('ix_raw_articles_created_at', table_name='raw_articles')
    op.drop_index('ix_saved_articles_saved_at', table_name='saved_articles')
    op.drop_index('ix_accounts_created_at', table_name='accounts')
    op.drop_index('ix_shared_cards_created_at', table_name='shared_cards')
