"""Agent communication protocol — re-exports from schemas for backward compatibility."""

from null_engine.models.schemas import AgentMessage, ConversationTurn

__all__ = ["AgentMessage", "ConversationTurn"]
