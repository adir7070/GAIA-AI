from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base


class Feedback(Base):
    """Stores corrections users make to AI suggestions for future training."""

    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    suggestion_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    contact_id: Mapped[int | None] = mapped_column(
        ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True
    )
    incoming_message: Mapped[str] = mapped_column(Text, nullable=False)
    original: Mapped[str] = mapped_column(Text, nullable=False)
    edited: Mapped[str] = mapped_column(Text, nullable=False)
    delta_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    decision: Mapped[str] = mapped_column(String(16), default="edit", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
