from typing import Annotated
from fastapi import Depends, APIRouter, Form, HTTPException, UploadFile, File
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import EmailStr

from database.database import get_db
from repositories.subscriptions import SubRepository
from security.auth import get_current_user
from security.roles_access import require_user
from services.auth_service import AuthService
from services.profile_service import ProfileService
from services.sub_buy_service import SubsService
from templates.template_config import template

router = APIRouter(prefix="/buy", tags=["Buy"])

@router.get("/")
async def buy_page(request: Request, current_user = Depends(get_current_user), db = Depends(get_db), user = Depends(require_user)):
    active_sub = await SubRepository.get_by_id(current_user.id, db)

    return template.TemplateResponse(
        request=request,
        name="sub_buy/buy.html",
        context={"a_sub": active_sub}
    )

@router.post("/")
async def buy(request: Request, plan: str = Form(), current_user = Depends(get_current_user), db = Depends(get_db)):
   sub = await SubsService.buy(plan, current_user, db)
   if not sub["success"]:
       return template.TemplateResponse(
           request=request,
           name="sub_buy/buy.html",
           context={"e": str(sub["message"])}
       )

   return template.TemplateResponse(
       request=request,
       name="sub_buy/buy.html",
       context={"e": "Your subscription was successfully activated"}
   )