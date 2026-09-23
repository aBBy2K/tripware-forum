from sqlalchemy import Integer, String, Boolean, ForeignKey, Text, DateTime, func
from sqlalchemy.orm import mapped_column, Mapped, relationship
from datetime import datetime

from models.users import Users
from database.database import Base

class Messages(Base):
    __tablename__ = "messages"

    sender_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    recipient_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    msg: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    sender: Mapped["Users"] = relationship(foreign_keys=[sender_id])
    recipient: Mapped["Users"] = relationship(foreign_keys=[recipient_id])
    imgs: Mapped[list["ImgsInMSGS"]] = relationship(back_populates="msg")

class ImgsInMSGS(Base):
    __tablename__ = "imgs_in_msgs"

    pic_path: Mapped[str] = mapped_column(String(128))
    msg_id: Mapped[int] = mapped_column(Integer, ForeignKey("messages.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    msg: Mapped["Messages"] = relationship(foreign_keys=[msg_id], back_populates="imgs")

class ChatboxMSGS(Base):
    __tablename__ = "chatbox_msgs"

    sender_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    msg: Mapped[str] = mapped_column(Text)

    sender: Mapped["Users"] = relationship(foreign_keys=[sender_id])