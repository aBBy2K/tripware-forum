from typing import Annotated
from fastapi import Depends, APIRouter, Form, HTTPException, UploadFile, File
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import EmailStr

from database.database import get_db
from security.auth import get_current_user
from services.account import AccountService
from services.auth_service import AuthService
from services.profile_service import ProfileService
from templates.template_config import template

router = APIRouter(prefix="/account", tags=["Account"])

@router.get("/settings")
async def settings_page(request: Request, current_user = Depends(get_current_user), db = Depends(get_db)):
    return template.TemplateResponse(
        request=request,
        name="profile/account_edit.html",
        context={"current_user": current_user}
    )

@router.post("/settings")
async def settings(request: Request, doEmailNotifs: bool | None = Form(None), current_user = Depends(get_current_user), db = Depends(get_db)):
    result = await AccountService.edit_profile(doEmailNotifs, db, current_user)

    return template.TemplateResponse(
        request=request,
        name="profile/account_edit.html",
        context={"current_user": current_user, "e": str(result["message"])}
    )

@router.get("/tglink")
async def tglink(request: Request, current_user = Depends(get_current_user), db = Depends(get_db)):
    if not current_user.telegram_chat_id:
        return await AccountService.tg_generate_token(db, current_user)
    else:
        return await AccountService.tgunlink(current_user, db)