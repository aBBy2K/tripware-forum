from fastapi import HTTPException

from repositories.notifications import NotificationsRepository
from repositories.users import UsersRepository
from websocket.manager import manager


class NotificationsService:
    @staticmethod
    async def add_notif(n_type, head, body, is_read, user_id, db):
        user = await UsersRepository.get_by_id(db, user_id)

        if not user:
            raise HTTPException(
                status_code=404,
                detail="user not found"
            )

        notification = await NotificationsRepository.add_notification(n_type, head, body, is_read, user_id, db)

        await manager.notify(user_id, {
            "head": head,
            "body": body,
            "type": n_type
        })

        return notification