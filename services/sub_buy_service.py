from repositories.subscriptions import SubRepository

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