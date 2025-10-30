"""
Invitation Model
"""
from datetime import datetime, timedelta
from sqlalchemy import String, DateTime, Enum, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import uuid

from app.db.base_class import Base
from app.models.user import UserRole


class Invitation(Base):
    """Invitation model for user registration"""
    __tablename__ = "invitations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    token: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, length=20),
        nullable=False,
        default=UserRole.TRADER
    )

    # Tracking
    created_by_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    used_by_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.utcnow() + timedelta(days=7)
    )

    # Relationships
    created_by: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by_id],
        lazy="select"
    )
    used_by: Mapped["User"] = relationship(
        "User",
        foreign_keys=[used_by_id],
        lazy="select"
    )

    @property
    def is_valid(self) -> bool:
        """Check if invitation is still valid"""
        return (
            self.used_at is None and
            self.expires_at > datetime.utcnow()
        )

    @staticmethod
    def generate_token() -> str:
        """Generate a unique invitation token"""
        return str(uuid.uuid4())

    def __repr__(self) -> str:
        return f"<Invitation(id={self.id}, email='{self.email}', role='{self.role}', valid={self.is_valid})>"
