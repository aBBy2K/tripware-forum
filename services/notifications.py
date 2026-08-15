from fastapi import HTTPException

from repositories.notifications import NotificationsRepository
from repositories.users import UsersRepository
from services.users import UsersService
from websocket.manager import manager


class NotificationsService:
    @staticmethod
    async def add_notif(n_type, head, body, is_read, user_id, db):
        user = await UsersService.get_user(user_id, db)

        if not user:
            raise HTTPException(
                status_code=404,
                detail="user not found"
            )

        notification = await NotificationsRepository.add_notification(n_type, head, body, is_read, user_id, db)

        await manager.notify(user_id, {
            "head": head,
            "body": body,
        })

        return notification

    @staticmethod
    async def mark_as_read(nid, current_user, db):
        notif = await NotificationsRepository.get_by_id(nid, db)

        if notif.user_id != current_user.id:
            return {"success": False, "message": "no permission"}
        else:
            res = await NotificationsRepository.mark_as_read(notif, current_user, db)
            return {"success": True}