"""ops_requests.send_error for SMTP failures

Revision ID: 007
Revises: 006
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("ops_requests", sa.Column("send_error", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("ops_requests", "send_error")
