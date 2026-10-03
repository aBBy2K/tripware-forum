from typing import Annotated
from fastapi import BackgroundTasks, Depends, APIRouter, Form, HTTPException, UploadFile, File, WebSocket
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import EmailStr
from database.database import get_db
from repositories.messages import MsgRepository
from repositories.users import UsersRepository
from security.auth import get_current_user, get_current_user_ws
from services.auth_service import AuthService
from services.dms_service import DMsServices
from services.profile_service import ProfileService
from services.users import UsersService
from templates.template_config import template
from services.gpt import GPTService
from dependencies.dependencies import get_gpt_service

router = APIRouter(prefix="/dms", tags=["DMs"])

@router.get("/")
async def messenger(request: Request, current_user = Depends(get_current_user), db = Depends(get_db)):
    chats = await MsgRepository.get_convos(current_user, db)

    return template.TemplateResponse(
        request=request,
        name="dms/messenger.html",
        context={"chats": chats}
    )

@router.get("/{user_id}")
async def chat_page(request: Request, user_id: int, db = Depends(get_db), current_user = Depends(get_current_user)):
    recipient = await UsersService.get_user(user_id, db)

    if not recipient:
        return template.TemplateResponse(
            request=request,
            name="dms/chat.html",
            context={"e": "User not found"}
        )

    messages = await MsgRepository.get_messages(current_user, user_id, db)

    return template.TemplateResponse(
        request=request,
        name="dms/chat.html",
        context={"current_user": current_user, "recipient": recipient, "messages": messages}
    )

@router.websocket("/ws")
async def ws(ws: WebSocket, current_user = Depends(get_current_user_ws)):
    print(
        "WS CONNECTED:",
        current_user.id
    )

    result = await DMsServices.ws(ws, current_user)

@router.websocket("/ai/ws")
async def ai_ws(ws: WebSocket, current_user = Depends(get_current_user_ws), gpt_service: GPTService = Depends(get_gpt_service)):
    print(
        "WS CONNECTED:",
        current_user.id
    )

    result = await DMsServices.ai_ws(ws, current_user, gpt_service)