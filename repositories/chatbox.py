from sqlalchemy import select
from sqlalchemy.orm import selectinload

from models.messages import ChatboxMSGS

class CBMSGSRepository:
    @classmethod
    async def create(cls, sender, msg, db):
        try:
            message = ChatboxMSGS(sender_id=sender, msg=msg)
            db.add(message)
            await db.commit()
            await db.refresh(message)
            return message
        except Exception as e:
            print(f"internal error has occurred while trying to send message to db: {e}")
            await db.rollback()

    @classmethod
    async def get(cls, db):
        stmt = select(ChatboxMSGS).options(selectinload(ChatboxMSGS.sender))
        result = await db.scalars(stmt)
        return result.all()
