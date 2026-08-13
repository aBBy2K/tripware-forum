# from typing import Annotated
# from fastapi import Depends, APIRouter, Form, HTTPException, UploadFile, File, WebSocket
# from fastapi.requests import Request
# from fastapi.staticfiles import StaticFiles
# from fastapi.responses import RedirectResponse
# from pydantic import EmailStr
# from database.database import get_db
# from repositories.messages import MsgRepository
# from repositories.users import UsersRepository
# from security.auth import get_current_user, get_current_user_ws
# from services.auth_service import AuthService
# from services.chatbox_service import CBService
# from services.dms_service import DMsServices
# from services.profile_service import ProfileService
# from templates.template_config import template
#
# router = APIRouter(prefix="/", tags=["ChatBox"])
#
# @router.websocket("/ws")
# async def ws(websocket: WebSocket, current_user = Depends(get_current_user_ws), db = Depends(get_db)):
#     message = await CBService.ws(websocket, current_user, db)