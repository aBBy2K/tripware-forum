from datetime import datetime

from sqlalchemy import Integer, String, Boolean, ForeignKey, Text, DateTime
from sqlalchemy.orm import mapped_column, Mapped, relationship

from models.users import Users
from database.database import Base

class Subs(Base):
    __tablename__ = "subscription"

    plan_id: Mapped[int] = mapped_column(Integer, ForeignKey("sub_plans.id"))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True)
    started_at: Mapped[datetime] = mapped_column(DateTime)
    expires_at: Mapped[datetime] = mapped_column(DateTime)

    plan: Mapped["SubPlans"] = relationship(foreign_keys=[plan_id])
    user: Mapped["Users"] = relationship(foreign_keys=[user_id])

class SubPlans(Base):
    __tablename__ = "sub_plans"

    days: Mapped[int] = mapped_column(Integer)