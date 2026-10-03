from fastapi import HTTPException, BackgroundTasks
from passlib.hash import bcrypt
from pydantic import EmailStr
from fastapi.responses import RedirectResponse

from core.redis_conf import redis
from models.users import Users
from repositories.users import UsersRepository
from schemas.users import UsersCreate, PasswordReset
from secrets import token_hex

from security.email import verification_email, password_recovery_email
from security.auth import create_access_key

class AuthService:
    @staticmethod
    async def register(login: str, password: str, c_password: str, email: EmailStr, name: str, db, bgtask: BackgroundTasks):
        user_e = await UsersRepository.get_by_login(db, login=login)
        if user_e:
            return {
                "success": False,
                "message": "Login is already taken"
            }
        email_e = await UsersRepository.get_by_email(db, email=email)
        if email_e:
            return {
                "success": False,
                "message": "Email is already taken"
            }

        if password != c_password:
            return {
                "success": False,
                "message": "Passwords don't match"
            }

        try:
            u = UsersCreate(login=login, password=password, email=email, name=name)

            token = token_hex(16)

            user = await UsersRepository.create_user(login=u.login, password=u.password, email=u.email, name=u.name, token=token, db=db)


            await redis.set(
                f"user:{user.id}:token",
                token,
                ex=600
            )
            
            bgtask.add_task(verification_email, email, token)

        except ValueError as e:
            return {
                "success": False,
                "message": e
            }
        except Exception as e:
            await db.rollback()
            return {
                "success": False,
                "message": e
            }

        return {
            "success": True
        }

    @staticmethod
    async def verify(token: str, db):
        error = {
            "success": False,
            "message": "Couldn't verify token"
        }

        token_e = await UsersRepository.get_by_token(db, token)
        if not token_e:
            return error

        token_r = await redis.get(f"user:{token_e.id}:token")

        if not token_r:
            return error

        token_e.is_verified = True
        await db.commit()
        await redis.delete(f"user:{token_e.id}:token")

        return {
            "success": True
        }

    @staticmethod
    async def login(login: str, password: str, db):
        user = await UsersRepository.get_by_login(db, login)

        cred = {
                "success": False,
                "message": f"Wrong credentials"
            }

        if not user:
            return cred

        if not bcrypt.verify(password, user.password):
            return cred

        access_token = create_access_key(data={"sub": str(user.id)})

        return {
            "success": True,
            "access_token": access_token
        }

    @staticmethod
    async def password_recovery(email: EmailStr, db, bgtask: BackgroundTasks):
        user = await UsersRepository.get_by_email(db, email)
        resmsg = {"success": False, "message": "An email with password recovery instruction will be sent if user with this email exists"}

        if not user:
            return resmsg
        else:
            old_token = user.verification_token

            token = token_hex(16)

            await UsersRepository.set_token(db, token, old_token)

            bgtask.add_task(password_recovery_email, email, token)

            return resmsg

    @staticmethod
    async def recovery_verify(token, db):
        is_e = await UsersRepository.get_by_token(db, token)

        if not is_e:
            return {"success": False, "message": "Verification token error"}
        else:
            # n_token = token_hex(16)
            # await UsersRepository.set_token(db, n_token)

            return {"success": True}

    @staticmethod
    async def reset_password(password, c_password, token, db):
        if password != c_password:
            return {"success": False, "message": "Passwords doesn't match"}

        p = PasswordReset(password=password)

        await UsersRepository.reset_password(p.password, token, db)

        return {"success": True}