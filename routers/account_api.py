from typing import Annotated
from fastapi import Depends, APIRouter, Form, HTTPException, UploadFile, File
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import EmailStr

from database.database import get_db
from security.auth import get_current_user
from services.auth_service import AuthService
from services.profile_service import ProfileService
from templates.template_config import template

router = APIRouter(prefix="/account", tags=["Account"])

@router.get("/settings")
def settings_page(request: Request, current_user = Depends(get_current_user)):
    return template.TemplateResponse(
        request=request,
        name="profile/account_edit.html",
        context={"user": current_user}
    )