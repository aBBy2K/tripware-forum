import json
from datetime import datetime

from fastapi import HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.redis_conf import redis
from database.database import get_db
from repositories.forum import ForumRepository
from repositories.users import UsersRepository


class UsersService:
    @staticmethod
    async def get_user(uid, db):
        cached = await redis.get(f"user:{uid}")
        if cached:
            user = json.loads(cached)

            user["last_seen"] = datetime.fromisoformat(user["last_seen"])

            return user
        
        user_db = await UsersRepository.get_by_id(db, uid)

        if not user_db:
            return {"success": False, "message": "user not found"}

        user = {
            "id": user_db.id,
            "login": user_db.login,
            "email": user_db.email,
            "name": user_db.name,
            "pfp": user_db.pfp,
            "role_id": user_db.role_id,
            "last_seen": user_db.last_seen.isoformat(),
            "is_banned": user_db.is_banned,
            "ban_reason": user_db.ban_reason,
            "is_verified": user_db.is_verified,
            "do_email_notifications": user_db.do_email_notifications,
            "telegram_chat_id": user_db.telegram_chat_id,

            "role": {
                "id": user_db.role.id,
                "name": user_db.role.name,
            },
        }

        await redis.set(
            f"user:{uid}",
            json.dumps(user),
            ex=300
        )

        user["last_seen"] = datetime.fromisoformat(user["last_seen"])

        return user

    @staticmethod
    async def online_check(uid):
        return await redis.sismember("online_users", uid)

    @staticmethod
    async def set_online(dt, uid, db: AsyncSession):
        await UsersRepository.set_last_seen(dt, uid, db)

    @staticmethod
    async def sub_unsub(follower, followee, db):
        is_sub = await UsersRepository.get_follow(follower, followee, db)

        if is_sub:
            await UsersRepository.unsubscribe(follower, followee, db)
        else:
            await UsersRepository.subscribe(follower, followee, db)

        return {"success": True}