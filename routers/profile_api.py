from typing import Annotated
from fastapi import Depends, APIRouter, Form, HTTPException, UploadFile, File
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import EmailStr
from starlette.websockets import WebSocket

from database.database import get_db
from repositories.notifications import NotificationsRepository
from repositories.users import UsersRepository
from security.auth import get_current_user, get_current_user_ws
from services.auth_service import AuthService
from services.notifications import NotificationsService
from services.profile_service import ProfileService
from services.users import UsersService
from templates.template_config import template

router = APIRouter(prefix="/profile", tags=["Profile"])

@router.get("/")
async def profile_page(request: Request, current_user = Depends(get_current_user), db = Depends(get_db)):
    stats = await UsersRepository.get_profile_stats(current_user.id, db)

    return template.TemplateResponse(
        request=request,
        name="profile/profile.html",
        context={"current_user": current_user, "subs_count": stats["followers"], "subbed_count": stats["followings"]}
    )

@router.get("/notifications")
async def notifications_page(request: Request, current_user = Depends(get_current_user), db = Depends(get_db)):
    notifications = await NotificationsRepository.get_all(current_user, db)

    return template.TemplateResponse(
        request=request,
        name="/profile/notifs.html",
        context={"notifs": notifications}
    )

@router.websocket("/notifications/ws")
async def notifications_ws(websocket: WebSocket, current_user = Depends(get_current_user_ws)):
    await NotificationsService.ws(websocket, current_user)

@router.get("/notifications/{nid}/read")
async def notifications_page(request: Request, nid: int, current_user = Depends(get_current_user), db = Depends(get_db)):
    res = await NotificationsService.mark_as_read(nid, current_user, db)

    if not res["success"]:
        raise HTTPException(
            status_code=403,
            detail=str(res["message"])
        )

    ref_url = request.headers.get("referer")

    if not ref_url:
        ref_url = "/"

    return RedirectResponse(
        url=ref_url
    )
@router.get("/logout")
def logout(request: Request):
    response = RedirectResponse(
        status_code=303,
        url="/auth/login"
    )
    response.delete_cookie("token")

    return response

@router.get("/edit")
def edit_page(request: Request, current_user = Depends(get_current_user), db = Depends(get_db)):
    return template.TemplateResponse(
        request=request,
        name="profile/profile_settings.html",
        context={"current_user": current_user}
    )

@router.post("/edit")
async def edit(request: Request, db = Depends(get_db), current_user = Depends(get_current_user), name: str | None = Form(None), pfp: Annotated[UploadFile | None, File()] = None):
    result = await ProfileService.edit(db=db, current_user=current_user, name=name, pfp=pfp)

    if not result["success"]:
        return template.TemplateResponse(
            request=request,
            name="profile/profile_settings.html",
            context={"current_user": current_user, "e": result["message"]}
        )

    return template.TemplateResponse(
        request=request,
        name="profile/profile_settings.html",
        context={"current_user": current_user, "e": result["message"]}
    )

@router.get("/subs")
async def subs_page(request: Request, db = Depends(get_db), current_user = Depends(get_current_user)):
    subs = await UsersRepository.get_followers(current_user.id, db)

    subs_list = []

    for sub in subs:
        target = await UsersService.get_user(sub, db)
        subs_list.append(target)


    return template.TemplateResponse(
        request=request,
        name="users/followers.html",
        context={"subs": subs_list}
    )

@router.get("/subbed")
async def subs_page(request: Request, db = Depends(get_db), current_user = Depends(get_current_user)):
    subbed = await UsersRepository.get_followings(current_user.id, db)

    subbed_list = []

    for sub in subbed:
        target = await UsersService.get_user(sub, db)
        subbed_list.append(target)


    return template.TemplateResponse(
        request=request,
        name="users/followings.html",
        context={"subs": subbed_list}
    )