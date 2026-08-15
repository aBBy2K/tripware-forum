from typing import Annotated, Optional

import math
from fastapi import Depends, APIRouter, Form, HTTPException, UploadFile, File
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import EmailStr
from starlette.websockets import WebSocket, WebSocketDisconnect

from core.redis_conf import redis
from database.database import get_db, SessionLocal
from repositories.admin_forum import AdminForumRepository
from repositories.forum import ForumRepository
from security.auth import get_current_user, get_current_user_ws
from security.roles_access import can_post
from services.auth_service import AuthService
from services.forum import ForumService
from services.profile_service import ProfileService
from templates.template_config import template
from websocket.manager import manager

router = APIRouter(prefix="/forum", tags=["Forum"])


async def required_role(subcat_id: int, db=Depends(get_db), current_user=Depends(get_current_user)):
    subcategory = await AdminForumRepository.get_subcat_by_id(subcat_id, db)

    if not subcategory:
        raise HTTPException(
            status_code=404,
            detail="subcat not found"
        )

    if not can_post(subcategory, current_user):
        raise HTTPException(
            status_code=403,
            detail="no permission"
        )

    return subcategory

@router.get("/search")
async def search(request: Request, q: str = "", db = Depends(get_db), current_user = Depends(get_current_user)):
    posts = []
    if q.strip():
        posts = await ForumRepository.search(q, db)

    return template.TemplateResponse(
        request=request,
        name="forum/search.html",
        context={"posts": posts, "q": q}
    )

@router.get("/post/{post_id}")
async def post_page(request: Request, post_id: int, db = Depends(get_db), current_user = Depends(get_current_user)):
    post = await ForumService.get_post(post_id, db, current_user)

    if not post:
        raise HTTPException(
            status_code=404,
            detail="post not found"
        )

    comments = await ForumRepository.get_post_comments(post_id, db)
    # is_liked = await ForumRepository.get_user_post_like(post_id, current_user, db)
    # liked_ids = await ForumRepository.get_liked_cmnts_ids(post_id, current_user, db)
    # likes_count = await ForumRepository.get_post_stats(post_id, db)

    await redis.incr(f"post:{post_id}:views")
    likes_count = await redis.scard(f"post:{post_id}:likes")

    is_liked = await redis.sismember(
        f"post:{post_id}:likes",
        current_user.id
    )

    return template.TemplateResponse(
        request=request,
        name="forum/post.html",
        context={"post": post["post"], "allow_comments": post["allow_comments"], "comments": comments, "is_liked": is_liked, "liked": post["likes_uids"], "current_user": current_user, "likes": likes_count}
    )

@router.get("/post/{post_id}/report")
async def report_page(request: Request, post_id: int, db = Depends(get_db), current_user = Depends(get_current_user)):
    return template.TemplateResponse(
        request=request,
        name="forum/report.html"
    )

@router.post("/post/{post_id}/report")
async def report(request: Request, post_id: int, reason: str = Form(), additional_info: str | None = Form(None), db = Depends(get_db), current_user = Depends(get_current_user)):
    rep = await ForumService.report(post_id, current_user.id, reason, additional_info, db)

    return template.TemplateResponse(
        request=request,
        name="forum/report.html",
        context={"e": rep["message"]}
    )

@router.get("/post/{post_id}/delete")
async def delete_post(request: Request, post_id: int, db = Depends(get_db), current_user = Depends(get_current_user), is_reported: bool | None = None, uid: int | None = None):
    #uid пользователя который пожаловался на пост

    post = await ForumRepository.get_post_by_id(post_id, db)

    if not post:
        raise HTTPException(
            status_code=404,
            detail="post not found"
        )

    await ForumService.delete_post(post_id, db, is_reported, uid, current_user)
    return RedirectResponse(
        status_code=303,
        url=f"/forum/sc/{post.subcategory.id}"
    )

@router.post("/post/{post_id}")
async def leave_comment(request: Request, post_id: int, comment: str = Form(), db = Depends(get_db), current_user = Depends(get_current_user)):
    new_comment = await ForumService.new_comment(comment, post_id, db, current_user)
    return RedirectResponse(
        status_code=303,
        url=f"/forum/post/{post_id}"
    )

@router.get("/post/{post_id}/like")
async def like_unlike(request: Request, post_id: int, db = Depends(get_db), current_user = Depends(get_current_user)):
    result = await ForumService.like_unlike(post_id, db, current_user)

    return RedirectResponse(
        url=f"/forum/post/{post_id}"
    )

@router.websocket("/post/ws/{post_id}")
async def like_unlike_ws(ws: WebSocket, post_id: int, current_user = Depends(get_current_user_ws)):
    await ws.accept()
    await manager.post_connect(post_id, ws)

    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        await manager.post_disconnect(post_id, ws)

@router.get("/comment/{cid}/like")
async def l_ul_comment(request: Request, cid: int, db = Depends(get_db), current_user = Depends(get_current_user)):
    l_ul = await ForumService.like_unlike_comment(cid, db, current_user)
    post = await ForumRepository.get_pid_by_cid(cid, db)

    return RedirectResponse(
        url=f"/forum/post/{post}/#{cid}"
    )

@router.get("/comment/{cid}/delete")
async def delete_comment(request: Request, cid: int, db = Depends(get_db), current_user = Depends(get_current_user)):
    ref = request.headers.get("Referer")

    if not ref:
        ref = "/"

    delete = await ForumService.delete_comment(cid, db, current_user)

    if delete["success"]:
        return RedirectResponse(
            url=ref
        )
    else:
        return {"message": "An error has occurred"}

@router.get("/sc/{subcat_id}")
async def subcategory_page(request: Request, subcat_id: int, db = Depends(get_db), current_user = Depends(get_current_user), page: int = 1):
    subcat = await AdminForumRepository.get_subcat_by_id(subcat_id, db)
    if not subcat:
        raise HTTPException(
            status_code=404,
            detail="subcategory not found"
        )

    if subcat.category.required_role is not None and current_user.role.name != "Admin" and current_user.role.name != subcat.category.required_role:
        return RedirectResponse(
            url="/profile"
        )

    total_posts = await ForumRepository.get_posts_count_subcat(subcat, db)

    total_pages = math.ceil(total_posts / 10)

    page = min(page, total_pages)
    page = max(page, 1)

    offset = (page - 1) * 10

    pinned_posts = await ForumRepository.get_pinned_posts_by_sc(subcat_id, db)
    posts = await AdminForumRepository.get_subcat_posts(subcat_id, offset, db)
    return template.TemplateResponse(
        request=request,
        name="forum/subcat.html",
        context={"posts": posts, "pinned_posts": pinned_posts, "subcat": subcat, "user": current_user, "can_post": can_post(subcat, current_user), "page": page, "pages": total_pages}
    )

@router.get("/{subcat_id}/new")
async def new_post_page(request: Request, subcat_id: int, db = Depends(get_db), current_user = Depends(get_current_user)):
    subcat = await AdminForumRepository.get_subcat_by_id(subcat_id, db)
    if not subcat:
        raise HTTPException(
            status_code=404,
            detail="subcategory not found"
        )
    return template.TemplateResponse(
        request=request,
        name="forum/newpost.html"
    )

@router.post("/{subcat_id}/new")
async def new_post(request: Request, subcat_id: int, db = Depends(get_db), current_user = Depends(get_current_user), post_title: str = Form(), post_body: str = Form(), imgs: list[UploadFile] = File(None), role = Depends(required_role)):
    post = await ForumService.create(title=post_title, body=post_body, imgs=imgs, subcat_id=subcat_id, current_user=current_user, db=db)

    if not post["success"]:
        return template.TemplateResponse(
            request=request,
            name="forum/newpost.html",
            context={"e": str(post["message"])}
        )

    return template.TemplateResponse(
        request=request,
        name="forum/newpost.html",
        context={"e": "Post successfully created"}
    )

@router.get("/post/{post_id}/edit")
async def edit_post_page(request: Request, post_id: int, db = Depends(get_db), current_user = Depends(get_current_user)):
    post = await ForumRepository.get_post_by_id(post_id, db)
    post_images = await ForumRepository.get_post_imgs_count(post_id, db)

    if current_user.role.name != "Admin" and current_user.id != post.author_id:
        raise HTTPException(
            status_code=403,
            detail="no permission"
        )

    return template.TemplateResponse(
        request=request,
        name="forum/edit_post.html",
        context={"post": post, "post_imgs": post_images}
    )

@router.post("/post/{post_id}/edit")
async def edit_post(request: Request, post_id: int, post_title: str | None = Form(None), post_body: str | None = Form(None), imgs: Annotated[list[UploadFile], File()] = [], allow_comms: bool = Form(False) , db = Depends(get_db), current_user = Depends(get_current_user)):
    print(f"allow_comms: {allow_comms}")
    print(f"type: ", type(allow_comms))

    post = await ForumRepository.get_post_by_id(post_id, db)

    if current_user.role.name != "Admin" and current_user.id != post.author_id:
        raise HTTPException(
            status_code=403,
            detail="no permission"
        )

    post_images = await ForumRepository.get_post_imgs_count(post_id, db)


    res = await ForumService.edit_post(post, post_title, post_body, imgs, post_images, allow_comms, db)

    return template.TemplateResponse(
        request=request,
        name="forum/edit_post.html",
        context={"post": post, "post_imgs": post_images, "e": str(res["message"])}
    )

@router.get("/post/{post_id}/pin")
async def pin_post(request: Request, post_id: int, current_user = Depends(get_current_user), db = Depends(get_db)):
    await ForumService.pin_unpin(post_id, current_user, db)

    ref_url = request.headers.get("referer")

    if not ref_url:
        ref_url = "/"

    return RedirectResponse(
        url=ref_url
    )