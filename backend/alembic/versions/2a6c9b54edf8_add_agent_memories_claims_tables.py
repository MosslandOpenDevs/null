"""add_agent_memories_claims_tables

Revision ID: 2a6c9b54edf8
Revises: 1a5b8a43fdc7
Create Date: 2026-02-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision: str = '2a6c9b54edf8'
down_revision: Union[str, None] = '1a5b8a43fdc7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Agent memories table
    op.create_table(
        'agent_memories',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', UUID(as_uuid=True), sa.ForeignKey('agents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('world_id', UUID(as_uuid=True), sa.ForeignKey('worlds.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tier', sa.String(10), nullable=False),
        sa.Column('content', JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_agent_memories_agent_id', 'agent_memories', ['agent_id'])
    op.create_index('ix_agent_memories_world_id', 'agent_memories', ['world_id'])

    # Claims table
    op.create_table(
        'claims',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('world_id', UUID(as_uuid=True), sa.ForeignKey('worlds.id', ondelete='CASCADE'), nullable=False),
        sa.Column('claim_text', sa.Text, nullable=False),
        sa.Column('category', sa.String(50), server_default='general'),
        sa.Column('confidence', sa.Float, server_default='0.5'),
        sa.Column('status', sa.String(20), server_default='proposed'),
        sa.Column('proposer_id', UUID(as_uuid=True), sa.ForeignKey('agents.id', ondelete='SET NULL'), nullable=True),
        sa.Column('faction_id', UUID(as_uuid=True), sa.ForeignKey('factions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_claims_world_id', 'claims', ['world_id'])
    op.create_index('ix_claims_status', 'claims', ['status'])

    # Claim votes table
    op.create_table(
        'claim_votes',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('claim_id', UUID(as_uuid=True), sa.ForeignKey('claims.id', ondelete='CASCADE'), nullable=False),
        sa.Column('agent_id', UUID(as_uuid=True), sa.ForeignKey('agents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('faction_id', UUID(as_uuid=True), sa.ForeignKey('factions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_claim_votes_claim_id', 'claim_votes', ['claim_id'])


def downgrade() -> None:
    op.drop_table('claim_votes')
    op.drop_table('claims')
    op.drop_table('agent_memories')
