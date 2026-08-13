from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from models.subscription import Subs, SubPlans

class SubRepository:
    @classmethod
    async def get_by_id(cls, uid, db):
        stmt = select(Subs).where(Subs.user_id == uid)
        sub = await db.scalars(stmt)
        return sub.one_or_none()

    @classmethod
    async def create(cls, plan, user, db):
        if int(plan) == 1:
            d = 30
        elif int(plan) == 2:
            d = 60
        else:
            d = 90

        if user.role.name == "User":
            user.role_id = 2

        sub = Subs(plan_id=int(plan), user_id=user.id, started_at=datetime.now(), expires_at=datetime.now() + timedelta(days=d))
        db.add(sub)
        await db.commit()
        await db.refresh(sub)
        return sub