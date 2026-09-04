from fastapi import Depends, APIRouter, Form, HTTPException
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import EmailStr
from starlette.background import BackgroundTasks
from core.redis.ratelimit import rate_limit

from database.database import get_db
from services.auth_service import AuthService
from services.users import UsersService
from templates.template_config import template

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.get("/login")
def login_page(request: Request):
    return template.TemplateResponse(
        request=request,
        name="auth/login.html"
    )

@router.post("/login")
async def login(request: Request, login: str = Form(), password: str = Form(), db = Depends(get_db)):
    ip = request.client.host
    await rate_limit(f"login:{ip}", 5)

    result = await AuthService.login(login=login, password=password, db=db)

    if not result["success"]:
        return template.TemplateResponse(
            request=request,
            name="auth/login.html",
            context={"e": result["message"], "login": login}
        )

    response = RedirectResponse(
        status_code=303,
        url="/profile"
    )

    response.set_cookie(
        key="token",
        value=result["access_token"],
        max_age=2592000
    )

    return response

@router.get("/register")
def register_page(request: Request):
    return template.TemplateResponse(
        request=request,
        name="auth/register.html"
    )

@router.post("/register")
async def register(request: Request, bgtask: BackgroundTasks, login: str = Form(), password: str = Form(), c_password: str = Form(), email: EmailStr = Form(), name: str = Form(), db = Depends(get_db), ):
    result = await AuthService.register(login=login, password=password, c_password=c_password, email=email, name=name, db=db, bgtask=bgtask)

    if not result["success"]:
        return template.TemplateResponse(
            request=request,
            name="auth/register.html",
            context={"e": result["message"], "login": login, "email": email, "name": name}
        )

    return template.TemplateResponse(
        request=request,
        name="auth/login.html",
        context={"e": "Verify your account thru email that was sent to your email address"}
    )

@router.get("/verify/{token}")
async def verify(request: Request, token: str, db = Depends(get_db)):
    result = await AuthService.verify(token=token, db=db)

    if not result["success"]:
        raise HTTPException(
            status_code=404,
            detail=result["message"]
        )

    return RedirectResponse(
        status_code=303,
        url="/auth/login"
    )


@router.get("/forgor")
async def forgor_page(request: Request):
    return template.TemplateResponse(
        request=request,
        name="auth/forgor.html"
    )

@router.post("/forgor")
async def forgor(request: Request, bgtask: BackgroundTasks, email: EmailStr = Form(), db = Depends(get_db)):
    result = await AuthService.password_recovery(email, db, bgtask)

    return template.TemplateResponse(
        request=request,
        name="auth/forgor.html",
        context={"e": str(result["message"])}
    )

@router.get("/forgor/verify/{token}")
async def forgor_verify(request: Request, token: str, db = Depends(get_db)):
    result = await AuthService.recovery_verify(token, db)

    if not result["success"]:
        raise HTTPException(
            status_code=403,
            detail=str(result["message"])
        )
    else:
        return template.TemplateResponse(
            request=request,
            name="auth/pwd_recovery.html"
        )

@router.post("/forgor/verify/{token}")
async def forgor_verify(request: Request, token: str, password: str = Form(), c_password: str = Form(), db = Depends(get_db)):
    result = await AuthService.reset_password(password, c_password, token, db)

    if not result["success"]:
        raise HTTPException(
            status_code=403,
            detail=str(result["message"])
        )
    else:
        return RedirectResponse(
            url="/auth/login",
            status_code=303
        )