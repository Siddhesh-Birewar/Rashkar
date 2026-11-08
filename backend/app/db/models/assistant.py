from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Float, Integer, ForeignKey, JSON, Boolean
from backend.app.db.session import Base
from backend.app.core.timezone import now_utc

class AssistantSessionModel(Base):
    """
    Assistant conversation session linked to a farmer and active farm context.
    """
    __tablename__ = "assistant_sessions"

    session_id = Column(String(50), primary_key=True, index=True)
    farmer_id = Column(String(50), nullable=False, index=True)
    farm_id = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime, default=now_utc)
    updated_at = Column(DateTime, default=now_utc, onupdate=now_utc)

class AssistantMessageModel(Base):
    """
    Grounded message history with source citations and safety audit metadata.
    """
    __tablename__ = "assistant_messages"

    message_id = Column(String(50), primary_key=True, index=True)
    session_id = Column(String(50), ForeignKey("assistant_sessions.session_id"), nullable=False, index=True)
    sender = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    retrieved_context_json = Column(JSON, default=dict)  # Grounding context from DB/assessments
    citations_json = Column(JSON, default=list)  # Referenced dataset IDs or advisory IDs
    provider_mode = Column(String(20), default="none")  # none, ollama, cloud
    model_name = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=now_utc)
