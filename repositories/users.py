from operator import and_
from secrets import token_hex

from sqlalchemy import select, delete, func, update
from sqlalchemy.orm import selectinload
from passlib.hash import bcrypt

from models.users import Users, UsersSubscribers


class UsersRepository:
    @classmethod
    async def create_user(cls, login, password, email, name, token, db):
        user = Users(login=login, password=bcrypt.hash(password), email=email, name=name, is_verified=False, verification_token=token)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @classmethod
    async def reset_password(cls, password, token, db):
        user = await UsersRepository.get_by_token(db, token)

        if user:
            n_token = token_hex(16)

            user.password = bcrypt.hash(password)
            user.verification_token = n_token
            await db.commit()

    @classmethod
    async def get_by_id(cls, db, uid: int):
        stmt = select(Users).where(Users.id == uid).options(selectinload(Users.role), selectinload(Users.sub), selectinload(Users.notifications))
        result = await db.scalars(stmt)
        return result.one_or_none()

    @classmethod
    async def get_by_login(cls, db, login: str):
        stmt = select(Users).where(Users.login == login)
        result = await db.scalars(stmt)
        return result.one_or_none()

    @classmethod
    async def get_by_email(cls, db, email: str):
        stmt = select(Users).where(Users.email == email)
        result = await db.scalars(stmt)
        return result.one_or_none()

    @classmethod
    async def set_token(cls, db, token: str, old_token: str):
        user = await UsersRepository.get_by_token(db, old_token)

        if not user:
            return
        else:
            user.verification_token = token
            await db.commit()

    @classmethod
    async def get_by_token(cls, db, token: str):
        stmt = select(Users).where(Users.verification_token == token)
        result = await db.scalars(stmt)
        return result.one_or_none()

    @classmethod
    async def subscribe(cls, follower, followee, db):
        sub = UsersSubscribers(follower_id=follower, followee_id=followee)
        db.add(sub)
        await db.commit()
        await db.refresh(sub)
        return sub

    @classmethod
    async def unsubscribe(cls, follower, followee, db):
        stmt = delete(UsersSubscribers).where(and_(UsersSubscribers.follower_id == follower, UsersSubscribers.followee_id == followee))
        unsub = await db.execute(stmt)
        await db.commit()
        return unsub

    @classmethod
    async def get_follow(cls, follower, followee, db):
        stmt = select(UsersSubscribers).where(and_(UsersSubscribers.follower_id == follower, UsersSubscribers.followee_id == followee))
        issub = await db.scalars(stmt)
        return issub.one_or_none()

    @classmethod
    async def get_followers(cls, user_id, db):
        stmt = select(UsersSubscribers.follower_id).where(UsersSubscribers.followee_id == user_id)
        subs = await db.scalars(stmt)
        return subs.all()

    @classmethod
    async def get_followings(cls, user_id, db):
        stmt = select(UsersSubscribers.followee_id).where(UsersSubscribers.follower_id == user_id)
        subs = await db.scalars(stmt)
        return subs.all()

    @classmethod
    async def get_profile_stats(cls, user_id, db):
        followers_stmt = select(func.count()).where(UsersSubscribers.followee_id == user_id)
        followings_stmt = select(func.count()).where(UsersSubscribers.follower_id == user_id)

        followers = await db.scalar(followers_stmt)
        followings = await db.scalar(followings_stmt)

        return {"followers": followers, "followings": followings}

    @classmethod
    async def set_last_seen(cls, dt, uid, db):
        stmt = update(Users).where(Users.id == uid).values(last_seen=dt)
        update_st = await db.execute(stmt)
        await db.commit()

    @classmethod
    async def set_tg_chatid(cls, chat_id, uid,  db):
        stmt = update(Users).where(Users.id == uid).values(telegram_chat_id=chat_id)
        await db.execute(stmt)
        await db.commit()
        return True

    @classmethod
    async def get_user_by_chatid(cls, chat_id, db):
        stmt = select(Users).where(Users.telegram_chat_id == chat_id)
        result = await db.scalars(stmt)
        return result.one_or_none()