from core.redis_conf import redis
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
import secrets

from database.database import SessionLocal
from repositories.users import UsersRepository
from services.telegram import TelegramService

class AccountService:
    @staticmethod
    async def edit_profile(doEmailNotifs, db, current_user):
        try:
            if doEmailNotifs:
                current_user.do_email_notifications = True
            else:
                current_user.do_email_notifications = False

            await db.commit()

            await redis.delete(f"user:{current_user.id}")

            return {"success": True, "message": f"Success"}

        except Exception as e:
            return {"success": False, "message": f"Something went wrong: {e}"}

    @staticmethod
    async def tg_generate_token(db, current_user):
        if current_user.telegram_chat_id:
            raise HTTPException(
                status_code=403,
                detail="you have already linked your telegram account"
            )

        token = secrets.token_urlsafe(16)

        await redis.set(
            f"tgtoken:{token}",
            current_user.id,
            ex=600
        )

        return RedirectResponse(
            url=f"https://t.me/tripwarebot?start={token}"
        )


    @staticmethod
    async def tglink(token, chat_id):
        uid = await redis.getdel(f"tgtoken:{token}")

        if not uid:
            await TelegramService.send_message("Unable to get token", chat_id)
            return {"success": False}

        async with SessionLocal() as db:
            user = await UsersRepository.get_user_by_chatid(chat_id, db)

        if user:
            await TelegramService.send_message("Account is already linked", chat_id)
            return {"success": False}

        async with SessionLocal() as db:
            ok = await UsersRepository.set_tg_chatid(chat_id, int(uid), db)

        if ok:
            await redis.delete(f"user:{uid}")
            await TelegramService.send_message("Success", chat_id)
            return {"success": True}

    @staticmethod
    async def tgunlink(current_user, db):
        await TelegramService.send_message("Unlinked", current_user.telegram_chat_id)
        
        current_user.telegram_chat_id = None

        await db.commit()

        await redis.delete(f"user:{current_user.id}")

        return {"success": True}