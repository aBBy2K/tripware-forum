from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Integer, String, Boolean, ForeignKey, Text, DateTime, func, BigInteger
from sqlalchemy.orm import mapped_column, Mapped, relationship
from database.database import Base

if TYPE_CHECKING:
    from models.subscription import Subs

class Users(Base):
    __tablename__ = "users"

    login: Mapped[str] = mapped_column(String(16))
    password: Mapped[str] = mapped_column(String(128))
    email: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(16))
    pfp: Mapped[str] = mapped_column(String(32), default="/static/uploads/pfps/def.png")
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id"), default=1)
    last_seen: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    ban_reason: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_token: Mapped[str] = mapped_column(String(32))
    do_email_notifications: Mapped[bool] = mapped_column(Boolean, default=False)
    telegram_chat_id: Mapped[int] = mapped_column(BigInteger, nullable=True, default=None)

    sub: Mapped["Subs | None"] = relationship(back_populates="user")
    notifications: Mapped[list["Notifications"]] = relationship(back_populates="user")
    role: Mapped["Roles"] = relationship(foreign_keys=[role_id])

class UsersSubscribers(Base):
    __tablename__ = "users_subscribers"

    follower_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    followee_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))

class Notifications(Base):
    __tablename__ = "notifications"

    type: Mapped[str] = mapped_column(String(32))
    head: Mapped[str] = mapped_column(String(32))
    body: Mapped[str] = mapped_column(Text)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["Users"] = relationship(foreign_keys=[user_id])

class Roles(Base):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(32))