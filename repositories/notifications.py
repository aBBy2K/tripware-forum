from sqlalchemy import select, delete, and_
from models.users import Notifications

class NotificationsRepository:
    @classmethod
    async def add_notification(cls, n_type, head, body, is_read, user_id, db):
        notif = Notifications(type=n_type, head=head, body=body, user_id=user_id, is_read=is_read)
        db.add(notif)
        await db.commit()
        await db.refresh(notif)
        return notif

    @classmethod
    async def get_all(cls, current_user, db):
        stmt = select(Notifications).where(and_(Notifications.is_read == False, Notifications.user_id == current_user.id)).order_by(Notifications.created_at.desc())
        notifications = await db.scalars(stmt)
        return notifications.all()

    @classmethod
    async def get_by_id(cls, nid, db):
        stmt = select(Notifications).where(Notifications.id == nid)
        notif = await db.scalars(stmt)
        return notif.one_or_none()

    @classmethod
    async def mark_as_read(cls, notification, current_user, db):
        notification.is_read = True
        await db.commit()