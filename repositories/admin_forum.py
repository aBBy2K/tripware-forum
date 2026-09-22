from sqlalchemy import select, and_, or_, delete
from sqlalchemy.orm import selectinload

from models import Users
from models.forum import Categories, SubCategories, Posts, Reports


class AdminForumRepository:
    @classmethod
    async def get_all_categories(cls, db):
        stmt = select(Categories)
        categories = await db.scalars(stmt)
        return categories.all()

    @classmethod
    async def get_cat_by_name(cls, name, db):
        stmt = select(Categories).where(Categories.name == name)
        category = await db.scalars(stmt)
        return category.all()

    @classmethod
    async def create_category(cls, name, vis, db):
        category = Categories(name=name, required_role=vis)
        db.add(category)
        await db.commit()
        await db.refresh(category)
        return category

    @classmethod
    async def get_all_subcats(cls, db):
        stmt = select(SubCategories).options(selectinload(SubCategories.category))
        subcats = await db.scalars(stmt)
        return subcats.all()

    @classmethod
    async def get_subcat_by_name(cls, name, db):
        stmt = select(SubCategories).where(SubCategories.name == name)
        subcategory = await db.scalars(stmt)
        return subcategory.all()

    @classmethod
    async def get_subcat_by_id(cls, scid, db):
        stmt = select(SubCategories).where(SubCategories.id == scid).options(selectinload(SubCategories.category))
        subcategory = await db.scalars(stmt)
        return subcategory.one_or_none()

    @classmethod
    async def get_subcat_posts(cls, scid, offset, db):
        stmt = select(Posts).where(and_(Posts.subcategory_id == scid, Posts.visibility_option == 1)).offset(offset).limit(10).order_by(Posts.created_at.desc()).options(selectinload(Posts.author))
        posts = await db.scalars(stmt)
        return posts.all()

    @classmethod
    async def create_subcategory(cls, name, cat, role, db):
        subcategory = SubCategories(name=name, category_id=int(cat), required_role=role)
        db.add(subcategory)
        await db.commit()
        await db.refresh(subcategory)
        return subcategory

    @classmethod
    async def get_post_by_id(cls, pid, db):
        stmt = select(Posts).where(Posts.id == pid).options(selectinload(Posts.author).selectinload(Users.role), selectinload(Posts.subcategory).selectinload(SubCategories.category), selectinload(Posts.images), selectinload(Posts.visibility))
        post = await db.scalars(stmt)
        return post.one_or_none()

    @classmethod
    async def ban(cls, user, reason, db):
        user.is_banned = True
        user.ban_reason = reason
        await db.commit()
        await db.refresh(user)
        return user

    @classmethod
    async def unban(cls, user, db):
        user.is_banned = False
        user.ban_reason = "user was banned before"
        await db.commit()
        await db.refresh(user)
        return user

    @classmethod
    async def get_reports(cls, db):
        stmt = select(Reports).options(selectinload(Reports.user), selectinload(Reports.post))
        reports = await db.scalars(stmt)
        return reports.all()

    @classmethod
    async def delete_report(cls, rid, db):
        stmt = delete(Reports).where(Reports.id == rid)
        delete_r = await db.execute(stmt)
        await db.commit()
        return delete_r

    @classmethod
    async def get_all_hidden_posts(cls, db):
        stmt = select(Posts).where(or_(Posts.visibility_option == 2, Posts.visibility_option == 3)).options(selectinload(Posts.author).selectinload(Users.role), selectinload(Posts.subcategory).selectinload(SubCategories.category), selectinload(Posts.images), selectinload(Posts.visibility))
        posts = await db.scalars(stmt)
        return posts.all()