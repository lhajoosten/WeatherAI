"""LLM audit model (core schema)."""

from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from .base import CoreBase


class LLMAudit(CoreBase):
    __tablename__ = "llm_audit"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    endpoint = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    prompt_summary = Column(String(200), nullable=False)
    tokens_in = Column(Integer, nullable=False)
    tokens_out = Column(Integer, nullable=False)
    cost = Column(Float, nullable=True)
    has_air_quality = Column(Boolean, nullable=True)
    has_astronomy = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="llm_audit")

__all__ = ["LLMAudit"]
