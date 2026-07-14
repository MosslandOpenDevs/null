"""Add per-world runner lease columns.

Prevents two workers (or a genesis task racing a manual /start) from
ticking the same world: a runner must hold and renew the lease.

Revision ID: 0002_runner_lease
Revises: 0001_baseline
Create Date: 2026-07-14
"""

import sqlalchemy as sa
from alembic import op

revision = "0002_runner_lease"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("worlds", sa.Column("lease_owner", sa.String(64), nullable=True))
    op.add_column("worlds", sa.Column("lease_expires_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("worlds", "lease_expires_at")
    op.drop_column("worlds", "lease_owner")
