from datetime import datetime
from sqlalchemy import select, and_, or_, delete, func, text, update, asc, desc, union, distinct
from sqlalchemy.orm import selectinload, aliased

from models import Users
from models.forum import Categories, SubCategories, Posts, PostComments, PostLikes, Reports, CommentsLikes, PostImages

SORTABLE = {
    "created_at": Posts.created_at,
    "title": Posts.title,
    "views": Posts.views
}

class ForumRepository:
    @classmethod
    async def search(cls, query, db, sort_by = "created_at", sort_order = "asc"):
        order_func = desc if sort_order == "desc" else asc
        column = SORTABLE.get(sort_by, Posts.created_at)

        stmt1 = select(Posts).where(text("MATCH(title, body) AGAINST(:q IN NATURAL LANGUAGE MODE)")).params(q=query)
        stmt2 = select(Posts).where(or_(
            Posts.title.like(f'%{query}%'),
            Posts.body.like(f'%{query}%')
        ))

        union_sq = union(stmt1, stmt2).subquery()

        posts_alias = aliased(Posts, union_sq)

        stmt = select(posts_alias).options(selectinload(posts_alias.author), selectinload(posts_alias.subcategory)).order_by(order_func(getattr(posts_alias, column.key))).limit(20)

        result = await db.scalars(stmt)

        return result.all()

    @classmethod
    async def get_pinned_posts_by_sc(cls, scid, db):
        stmt = select(Posts).where(and_(Posts.subcategory_id == scid, Posts.is_pinned == True))
        posts = await db.scalars(stmt)
        return posts.all()

    @classmethod
    async def create_post(cls, title: str, body: str, subcat_id: int, current_user, db):
        post = Posts(title=title, body=body, author_id=current_user.id, subcategory_id=subcat_id, created_at=datetime.now())
        db.add(post)
        await db.commit()
        await db.refresh(post)
        return post

    @classmethod
    async def get_post_by_id(cls, pid, db):
        stmt = select(Posts).where(Posts.id == pid).options(selectinload(Posts.subcategory).selectinload(SubCategories.category), selectinload(Posts.author).selectinload(Users.role), selectinload(Posts.images))
        post = await db.scalars(stmt)
        return post.one_or_none()

    @classmethod
    async def create_comment(cls, comment, pid, db, current_user):
        n_comment = PostComments(body=comment, post_id=pid, author_id=current_user.id, created_at=datetime.now())
        db.add(n_comment)
        await db.commit()
        await db.refresh(n_comment)

        result = await db.execute(
            select(PostComments)
            .options(selectinload(PostComments.author))
            .where(PostComments.id == n_comment.id)
        )

        return result.scalar_one()

    @classmethod
    async def get_post_comments(cls, pid, db):
        stmt = select(PostComments).where(PostComments.post_id == pid).options(selectinload(PostComments.author).selectinload(Users.role))
        comments = await db.scalars(stmt)
        return comments.all()

    @classmethod
    async def get_post_comments_pagination(cls, pid, db, offset):
        stmt = select(PostComments).where(PostComments.post_id == pid).options(selectinload(PostComments.author).selectinload(Users.role)).offset(offset).limit(5)
        comments = await db.scalars(stmt)
        return comments.all()

    @classmethod
    async def get_total_post_comms_count(cls, pid, db):
        stmt = select(func.count()).where(PostComments.post_id == pid)
        comms = await db.scalar(stmt)
        return comms

    @classmethod
    async def get_user_post_like(cls, pid, current_user, db):
        stmt = select(PostLikes).where(and_(PostLikes.user_id == current_user.id, PostLikes.post_id == pid))
        like = await db.scalar(stmt)
        return like

    @classmethod
    async def get_user_cmnt_like(cls, cid, current_user, db):
        stmt = select(CommentsLikes).where(and_(CommentsLikes.user_id == current_user.id, CommentsLikes.comment_id == cid))
        like = await db.scalar(stmt)
        return like

    @classmethod
    async def get_liked_cmnts_ids(cls, pid, current_user, db) -> set[int]:
        stmt = select(CommentsLikes.comment_id).join(PostComments, PostComments.id == CommentsLikes.comment_id).where(and_(PostComments.post_id == pid, CommentsLikes.user_id == current_user.id))
        result = await db.scalars(stmt)
        return set(result.all())

    @classmethod
    async def get_liked_cmnts_uids(cls, cid, db) -> set[int]:
        stmt = select(CommentsLikes.user_id).where(CommentsLikes.comment_id == cid)
        result = await db.scalars(stmt)
        return set(result.all())

    @classmethod
    async def get_pid_by_cid(cls, cid, db):
        stmt = select(PostComments.post_id).where(PostComments.id == cid)
        pid = await db.scalars(stmt)
        return pid.one_or_none()

    @classmethod
    async def like(cls, pid, db, current_user):
        like = PostLikes(post_id=pid, user_id=current_user.id)
        db.add(like)
        await db.commit()
        await db.refresh(like)
        return like

    @classmethod
    async def unlike(cls, pid, db, current_user):
        stmt = delete(PostLikes).where(and_(PostLikes.post_id == pid, PostLikes.user_id == current_user.id))
        unlike = await db.execute(stmt)
        await db.commit()
        return unlike

    @classmethod
    async def report(cls, pid, uid, reason, additional_info, db):
        report = Reports(post_id=pid, user_id=uid, reason=reason, additional_info=additional_info)
        db.add(report)
        await db.commit()
        await db.refresh(report)
        return report

    @classmethod
    async def delete_post(cls, pid, db):
        stmt = delete(Posts).where(Posts.id == pid)
        await db.execute(stmt)
        await db.commit()

    @classmethod
    async def get_comment_by_id(cls, cid, db):
        stmt = select(PostComments).where(PostComments.id == cid).options(selectinload(PostComments.author))
        comment = await db.scalars(stmt)
        return comment.one_or_none()

    @classmethod
    async def like_comment(cls, cid, current_user, db):
        like = CommentsLikes(comment_id=cid, user_id=current_user.id)
        db.add(like)
        await db.commit()
        await db.refresh(like)
        return like

    @classmethod
    async def unlike_comment(cls, cid, current_user, db):
        stmt = delete(CommentsLikes).where(and_(CommentsLikes.comment_id == cid, CommentsLikes.user_id == current_user.id))
        unlike = await db.execute(stmt)
        await db.commit()
        return unlike

    @classmethod
    async def delete_comment(cls, cid, current_user, db):
        stmt = delete(PostComments).where(PostComments.id == cid)
        delete_com = await db.execute(stmt)
        await db.commit()
        return delete_com

    @classmethod
    async def add_post_img(cls, paths: list, pid, db):
        for path in paths:
            image = PostImages(path=f"/{path}", post_id=pid)
            db.add(image)
            await db.commit()
            await db.refresh(image)
        return True

    @classmethod
    async def get_imgs_by_post(cls, pid, db):
        stmt = select(PostImages).where(PostImages.post_id == pid)
        imgs = await db.scalars(stmt)
        return imgs.all()

    @classmethod
    async def delete_imgs_from_db(cls, pid, db):
        stmt = delete(PostImages).where(PostImages.post_id == pid)
        await db.execute(stmt)
        await db.commit()

    @classmethod
    async def add_views(cls, pid, views, db):
        stmt = update(Posts).where(Posts.id == pid).values(views=Posts.views + views)
        await db.execute(stmt)
        await db.commit()

    @classmethod
    async def get_post_stats(cls, pid, db):
        stmt = select(func.count()).where(PostLikes.post_id == pid)
        likes = await db.scalar(stmt)
        return likes

    @classmethod
    async def get_post_likes(cls, pid, db):
        stmt = select(PostLikes.user_id).where(PostLikes.post_id == pid)
        likes = await db.scalars(stmt)
        return likes.all()

    @classmethod
    async def get_posts_count_subcat(cls, subcat, db):
        stmt = select(func.count()).where(Posts.subcategory_id == subcat.id)
        posts_in_sc = await db.scalar(stmt)
        return posts_in_sc

    @classmethod
    async def get_post_imgs_count(cls, pid, db):
        stmt = select(func.count()).where(PostImages.post_id == pid)
        imgs_c = await db.scalar(stmt)
        return imgs_c

    @classmethod
    async def pin(cls, pid, db):
        post = await ForumRepository.get_post_by_id(pid, db)
        post.is_pinned = True
        await db.commit()

    @classmethod
    async def unpin(cls, pid, db):
        post = await ForumRepository.get_post_by_id(pid, db)
        post.is_pinned = False
        await db.commit()

    @classmethod
    async def get_post_by_cid(cls, cid, db):
        stmt = select(PostComments.post_id).where(PostComments.id == cid)
        post = await db.scalars(stmt)
        return post.one_or_none()

    