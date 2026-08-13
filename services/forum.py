import json
import secrets

from fastapi import HTTPException
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from core.redis_conf import redis
from repositories.admin_forum import AdminForumRepository
from repositories.forum import ForumRepository
from schemas.posts import PostsUpdate, PostsCreate
from services.notifications import NotificationsService
from websocket.manager import manager

allowed_content_type = [
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/avif"
]

class ForumService:
    @staticmethod
    async def get_post(pid, db, current_user):
        cache = await redis.get(f"post:{pid}")

        if cache:
            post = json.loads(cache)

            if post["subcategory"]["category"]["required_role"] and current_user.role.name != "Admin" and current_user.role.name != post["subcategory"]["category"]["required_role"]:
                raise HTTPException(
                    status_code=403,
                    detail="no permission"
                )

            allow_comments = post["allow_comms"]

            print("[+] found in cache")
            return {"post": post, "allow_comments": allow_comments}
        else:
            print("[-] not found in cache")
            post = await AdminForumRepository.get_post_by_id(pid, db)

            if post.subcategory.category.required_role and current_user.role.name != "Admin" and current_user.role.name != post.subcategory.category.required_role:
                raise HTTPException(
                    status_code=403,
                    detail="no permission"
                )

            post_cache = {
                "id": post.id,
                "title": post.title,
                "body": post.body,
                "author_id": post.author_id,
                "subcategory_id": post.subcategory_id,
                "created_at": post.created_at.isoformat(),
                "views": post.views,
                "allow_comms": post.allow_comms,

                "author": {
                    "id": post.author.id,
                    "login": post.author.login,
                    "name": post.author.name,
                    "pfp": post.author.pfp,
                    "role": {
                        "id": post.author.role.id,
                        "name": post.author.role.name,
                    },
                },

                "subcategory": {
                    "id": post.subcategory.id,
                    "name": post.subcategory.name,
                    "required_role": post.subcategory.required_role,
                    "category": {
                        "id": post.subcategory.category.id,
                        "name": post.subcategory.category.name,
                        "required_role": post.subcategory.category.required_role,
                    },
                },

                "images": [
                    {
                        "id": image.id,
                        "path": image.path,
                    }
                    for image in post.images
                ],
            }

            await redis.set(
                f"post:{post.id}",
                json.dumps(post_cache),
                ex=300
            )

            print("[+] cached")

            allow_comments = post.allow_comms

            print("comments:", post.allow_comms)

            return {"post": post, "allow_comments": allow_comments}

    @staticmethod
    async def edit_post(post, post_title: str, post_body: str, imgs, aa_imgs, allow_comms: bool, db):
        cached = await redis.get(f"post:{post.id}")

        try:
            p = PostsUpdate(title=post_title, body=post_body, allow_comms=allow_comms)
        except Exception as e:
            return {
                "success": False,
                "message": f"Couldn't update post: {e}"
            }

        data = p.model_dump(exclude_none=True)

        if not data and not imgs:
            return {
                "success": False,
                "message": f"Couldn't update post: No valid data"
            }


        if imgs:
            if aa_imgs + len(imgs) > 5:
                raise HTTPException(
                    status_code=403,
                    detail="you can't choose more than 5 pictures"
                )

            for img in imgs:
                if not img or img.size == 0:
                    print("img size is less than 0")
                    continue

                if img.content_type not in allowed_content_type:
                    print("not allowed content type")
                    continue

                ext = img.filename.split(".")[-1]
                unique_name = secrets.token_hex(16)
                fullpath = f"static/uploads/post_imgs/{unique_name}.{ext}"

                content = await img.read()

                await run_in_threadpool(lambda p=fullpath, c=content: open(p, "wb").write(c))

                add_img = await ForumRepository.add_post_img(f"/{fullpath}", post.id, db)

        print("BEFORE:", post.allow_comms)

        for k, v in data.items():
            print("SETTING:", k, repr(v))
            setattr(post, k, v)
            print("AFTER SETATTR:", post.allow_comms)

        print("FINAL:", post.allow_comms)

        await db.commit()

        if cached:
            post_cache = {
                "id": post.id,
                "title": post.title,
                "body": post.body,
                "author_id": post.author_id,
                "subcategory_id": post.subcategory_id,
                "created_at": post.created_at.isoformat(),
                "views": post.views,
                "allow_comms": post.allow_comms,

                "author": {
                    "id": post.author.id,
                    "login": post.author.login,
                    "name": post.author.name,
                    "pfp": post.author.pfp,
                    "role": {
                        "id": post.author.role.id,
                        "name": post.author.role.name,
                    },
                },

                "subcategory": {
                    "id": post.subcategory.id,
                    "name": post.subcategory.name,
                    "required_role": post.subcategory.required_role,
                    "category": {
                        "id": post.subcategory.category.id,
                        "name": post.subcategory.category.name,
                        "required_role": post.subcategory.category.required_role,
                    },
                },

                "images": [
                    {
                        "id": image.id,
                        "path": image.path,
                    }
                    for image in post.images
                ],
            }

            await redis.set(
                f"post:{post.id}",
                json.dumps(post_cache),
                ex=300
            )

            print("[+] edit cached")

        return {
            "success": True,
            "message": "Post successfully updated"
        }



    @staticmethod
    async def sync_views(db):
        keys = await redis.keys("post:*:views")

        for key in keys:
            parts = key.split(":")
            pid = int(parts[1])
            views = int(await redis.get(key))

            await ForumRepository.add_views(pid, views, db)

            await redis.delete(key)

    @staticmethod
    async def create(title, body, imgs, subcat_id, current_user, db):
        try:
            p = PostsCreate(title=title, body=body)
        except ValidationError:
            return {"success": False, "message": "Title and body must be at least 5 characters long"}

        post = await ForumRepository.create_post(title=title, body=body, subcat_id=subcat_id, current_user=current_user, db=db)

        if imgs:
            print("got images", len(imgs))

            if len(imgs) > 5:
                raise HTTPException(
                    status_code=403,
                    detail="you can't choose more than 5 pictures"
                )

            for img in imgs:
                if not img or img.size == 0:
                    print("img size is less than 0")
                    continue

                if img.content_type not in allowed_content_type:
                    print("not allowed content type")
                    continue

                ext = img.filename.split(".")[-1]
                unique_name = secrets.token_hex(16)
                fullpath = f"static/uploads/post_imgs/{unique_name}.{ext}"

                content = await img.read()

                await run_in_threadpool(lambda p=fullpath, c=content: open(p, "wb").write(c))

                add_img = await ForumRepository.add_post_img(f"/{fullpath}", post.id, db)

        return {
            "success": True
        }

    @staticmethod
    async def new_comment(comment, pid, db, current_user):
        post = await ForumRepository.get_post_by_id(pid, db)

        if not post:
            raise HTTPException(
                status_code=404,
                detail="post not found"
            )

        if not post.allow_comms or post.subcategory.required_role != current_user.role.name:
            raise HTTPException(
                status_code=403,
                detail="no permission"
            )

        msg = await ForumRepository.create_comment(comment, pid, db, current_user)

        if current_user.id != post.author.id:
            await NotificationsService.add_notif(
                n_type="notification",
                head="User replied to your post",
                body=f"{current_user.name} replied to your post - '{post.title}'",
                is_read=False,
                user_id=post.author.id,
                db=db
            )

        return {
            "success": True
        }

    @staticmethod
    async def like_unlike(pid, db, current_user):
        is_liked = await ForumRepository.get_user_post_like(pid, current_user, db)
        stats = await ForumRepository.get_post_stats(pid, db)

        if is_liked:
            like = await ForumRepository.unlike(pid, db, current_user)
            await manager.post_updates(pid, data={
                "post_id": pid,
                "type": "unlike",
                "value": stats - 1
            })
        else:
            unlike = await ForumRepository.like(pid, db, current_user)
            await manager.post_updates(pid, data={
                "post_id": pid,
                "type": "like",
                "value": stats + 1
            })

        return {
            "success": True
        }

    @staticmethod
    async def delete_post(pid, db, is_reported, uid, current_user):
        post = await ForumRepository.get_post_by_id(pid, db)
        imgs = await ForumRepository.get_imgs_by_post(pid, db)

        if current_user.role.name == "Admin" or post.author.id == current_user.id:
            if imgs:
                await ForumRepository.delete_imgs_from_db(pid, db)

            cached = redis.get(f"post:{pid}")

            if cached:
                await redis.delete(f"post:{pid}")

            await ForumRepository.delete_post(pid, db)

            if is_reported:
                await NotificationsService.add_notif(
                    n_type="notification",
                    head="Thanks for your recent report",
                    body=f"Content that you recently reported got deleted",
                    is_read=False,
                    user_id=uid,
                    db=db
                )

            return True
        else:
            raise HTTPException(
                status_code=403,
                detail="no permission"
            )

    @staticmethod
    async def like_unlike_comment(cid, db, current_user):
        is_liked = await ForumRepository.get_user_cmnt_like(cid, current_user, db)

        if is_liked:
            like = await ForumRepository.unlike_comment(cid, current_user, db)
        else:
            unlike = await ForumRepository.like_comment(cid, current_user, db)

        return {
            "success": True
        }

    @staticmethod
    async def delete_comment(cid, db, current_user):
        comment = await ForumRepository.get_comment_by_id(cid, db)

        if current_user.role.name != "Admin" and comment.author.id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="no permission"
            )

        delete = await ForumRepository.delete_comment(cid, current_user, db)
        return {"success": True}

    @staticmethod
    async def report(pid, uid, reason, additional_info, db):
        add_rep = await ForumRepository.report(pid, uid, reason, additional_info, db)

        return {"message": "Reported"}

    @staticmethod
    async def pin_unpin(pid, current_user, db):
        if current_user.role.name != "Admin":
            raise HTTPException(
                status_code=403,
                detail="no permission"
            )

        post = await ForumRepository.get_post_by_id(pid, db)

        if not post:
            raise HTTPException(
                status_code=404,
                detail="not found"
            )

        if post.is_pinned:
            await ForumRepository.unpin(post, db)
        else:
            await ForumRepository.pin(post, db)