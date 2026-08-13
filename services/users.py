from fastapi import HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.redis_conf import redis
from database.database import get_db
from repositories.forum import ForumRepository
from repositories.users import UsersRepository


class UsersService:
    @staticmethod
    async def online_check(uid):
        return await redis.sismember("online_users", uid)

    @staticmethod
    async def set_online(dt, uid, db: AsyncSession):
        print(f"[*] updating last seen status for uid: {uid}: {dt}")
        await UsersRepository.set_last_seen(dt, uid, db)

    @staticmethod
    async def sub_unsub(follower, followee, db):
        # if followee.id == current_user.id:
        #     raise HTTPException(
        #         status_code=409,
        #         detail="you can't sub on yourself"
        #     )

        is_sub = await UsersRepository.get_follow(follower, followee, db)

        if is_sub:
            unsub = await UsersRepository.unsubscribe(follower, followee, db)
        else:
            sub = await UsersRepository.subscribe(follower, followee, db)

        return {"success": True}