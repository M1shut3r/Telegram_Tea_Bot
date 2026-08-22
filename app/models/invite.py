from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AdminInvite(Base):
    __tablename__ = "admin_invites"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    used_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    creator: Mapped["User"] = relationship(foreign_keys=[created_by])
    activated_user: Mapped["User | None"] = relationship(foreign_keys=[used_by])
