from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from charm.db.base import Base


class ProfileLike(Base):
    __tablename__ = "profile_like"

    a_profile: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("profile.id", ondelete="CASCADE"), primary_key=True
    )
    b_profile: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("profile.id", ondelete="CASCADE"), primary_key=True
    )

    liked_a: Mapped[bool | None] = mapped_column(Boolean)
    liked_b: Mapped[bool | None] = mapped_column(Boolean)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("a_profile < b_profile", name="profile_like_order_check"),
        Index("ix_profile_like_a_profile", "a_profile"),
        Index("ix_profile_like_b_profile", "b_profile"),
    )
