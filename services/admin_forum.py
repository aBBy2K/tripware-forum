from fastapi import HTTPException
from passlib.hash import bcrypt

from repositories.admin_forum import AdminForumRepository
from repositories.users import UsersRepository


class AdminForumService:
    @staticmethod
    async def add_cat(name, vis, db):
        is_exist = await AdminForumRepository.get_cat_by_name(name, db)

        if is_exist:
            return {
                "success": False,
                "message": "Category with this name is already exist"
            }

        if vis == "None":
            vis = None

        add_category = await AdminForumRepository.create_category(name, vis, db)
        return {
            "success": True
        }

    @staticmethod
    async def add_subcat(name, cat, role, db):
        is_exist = await AdminForumRepository.get_subcat_by_name(name, db)

        if is_exist:
            return {
                "success": False,
                "message": "Subcategory with this name is already exist"
            }

        if role == "None":
            role = None

        add_subcategory = await AdminForumRepository.create_subcategory(name, cat, role, db)
        return {
            "success": True
        }

    @staticmethod
    async def ban_unban(db, uid, reason):
        user = await UsersRepository.get_by_id(db, uid)

        if not user:
            raise HTTPException(
                status_code=404,
                detail="user not found"
            )

        if user.is_banned:
            unban = await AdminForumRepository.unban(user, db)
            msg = "User has been unbanned"
        else:
            ban = await AdminForumRepository.ban(user, reason, db)
            msg = f"User has been banned. Reason: {reason}"

        return {"message": msg}