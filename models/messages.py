from sqlalchemy import Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import mapped_column, Mapped, relationship

from models.users import Users
from database.database import Base

class Messages(Base):
    __tablename__ = "messages"

    sender_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    recipient_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    msg: Mapped[str] = mapped_column(Text)

    sender: Mapped["Users"] = relationship(foreign_keys=[sender_id])
    recipient: Mapped["Users"] = relationship(foreign_keys=[recipient_id])

class ChatboxMSGS(Base):
    __tablename__ = "chatbox_msgs"

    sender_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    msg: Mapped[str] = mapped_column(Text)

    sender: Mapped["Users"] = relationship(foreign_keys=[sender_id])