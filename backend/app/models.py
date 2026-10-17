from datetime import datetime

from sqlalchemy import JSON, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # What the employee sent
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255))
    text: Mapped[str] = mapped_column(Text)

    # What the LLM extracted (empty if extraction failed)
    category: Mapped[str | None] = mapped_column(String(20))
    urgency: Mapped[str | None] = mapped_column(String(10))
    language: Mapped[str | None] = mapped_column(String(2))
    summary: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float | None]
    other_topics: Mapped[list[str]] = mapped_column(JSON, default=list)

    # What the code decided
    queue: Mapped[str] = mapped_column(String(30))
    needs_review: Mapped[bool]
    review_reasons: Mapped[list[str]] = mapped_column(JSON, default=list)

    # The reply
    draft: Mapped[str] = mapped_column(Text)
    final_reply: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="new")
    edited: Mapped[bool] = mapped_column(default=False)