from repositories.subscriptions import SubRepository
from services.notifications import NotificationsService

class SubsService:
    @staticmethod
    async def buy(plan, current_user, db):
        active_sub = await SubRepository.get_by_id(current_user.id, db)
        if active_sub:
            return {
                "success": False,
                "message": "You already have an active subscription"
            }

        sub = await SubRepository.create(plan, current_user, db)
        return {
            "success": True,
            "sub": sub
        }

    @staticmethod
    async def deactivate(user, db):
        await SubRepository.delete(user, db)

        await NotificationsService.add_notif(
            n_type="notification",
            head="Expired subscription",
            body="Your subscription has expired",
            user_id=user.id,
            is_read=False,
            db=db
        )
