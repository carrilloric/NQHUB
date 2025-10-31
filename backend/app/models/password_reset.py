"""
Password Reset Token Model
"""
from datetime import datetime, timedelta, timezone
from sqlalchemy import String, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid

from app.db.base_class import Base


class PasswordResetToken(Base):
    """Password reset token model"""
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    token: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc) + timedelta(days=7)
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="password_reset_tokens")

    @staticmethod
    def generate_token() -> str:
        """Generate a unique reset token"""
        return str(uuid.uuid4())

    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not used and not expired)"""
        return (
            self.used_at is None and
            self.expires_at > datetime.now(timezone.utc)
        )

    def __repr__(self) -> str:
        return f"<PasswordResetToken(id={self.id}, user_id={self.user_id}, valid={self.is_valid})>"
