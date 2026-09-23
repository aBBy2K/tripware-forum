from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from models.messages import Messages, ImgsInMSGS
from models.users import Users


class MsgRepository:
    @classmethod
    async def create(cls, sender_id: int, recipient_id: int, msg: str, db):
        try:
            message = Messages(sender_id=sender_id, recipient_id=recipient_id, msg=msg)
            db.add(message)
            await db.commit()
            await db.refresh(message)
            return message
        except Exception as e:
            print(f"internal error has occurred while trying to send message to db: {e}")
            await db.rollback()

    @classmethod
    async def add_imgs(cls, msg_id, paths: list[str], db):
        if paths:
            for path in paths:
                img = ImgsInMSGS(pic_path=path, msg_id=msg_id)
            db.add(img)
            await db.commit()
            await db.refresh(img)
            return img

    @classmethod
    async def get_convos(cls, current_user, db):
        stmt1 = select(Messages.recipient_id).where(Messages.sender_id == current_user.id)
        stmt2 = select(Messages.sender_id).where(Messages.recipient_id == current_user.id)
        stmt = stmt1.union(stmt2)
        result = await db.scalars(stmt)
        convos = result.all()

        stmt = select(Users).where(Users.id.in_(convos))
        result = await db.scalars(stmt)
        return result.all()

    @classmethod
    async def get_messages(cls, current_user, user_id, db, limit = None):
        stmt = select(Messages).where(
            or_(
                and_(Messages.recipient_id == current_user.id, Messages.sender_id == user_id),
                and_(Messages.recipient_id == user_id, Messages.sender_id == current_user.id)
            )
        ).options(selectinload(Messages.sender), selectinload(Messages.imgs)).order_by(Messages.created_at.asc()).limit(limit)
        result = await db.scalars(stmt)
        return result.all()
