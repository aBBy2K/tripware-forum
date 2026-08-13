from fastapi import Depends, APIRouter
from fastapi.requests import Request
from starlette.responses import RedirectResponse
from starlette.websockets import WebSocket, WebSocketDisconnect

from database.database import get_db
from repositories.users import UsersRepository
from security.auth import get_current_user
from services.users import UsersService
from templates.template_config import template
from websocket.manager import manager

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/{user_id}")
async def user_page(request: Request, user_id: int, db = Depends(get_db), current_user = Depends(get_current_user)):
    user = await UsersRepository.get_by_id(db, user_id)
    is_followed = await UsersRepository.get_follow(current_user.id, user_id, db)
    is_online = await UsersService.online_check(user_id)
    return template.TemplateResponse(
        request=request,
        name="users/user_profile.html",
        context={"user": user, "is_f": is_followed, "is_o": is_online}
    )

@router.websocket("/{user_id}/ws")
async def user_page_ws(websocket: WebSocket, user_id: int):
    await websocket.accept()
    await manager.user_page_connect(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.user_page_disconnect(user_id, websocket)

@router.get("/{user_id}/sub")
async def sub_unsub(request: Request, user_id: int, db = Depends(get_db), current_user = Depends(get_current_user)):
     sub = await UsersService.sub_unsub(current_user.id, user_id, db)

     return RedirectResponse(
         url=f"/users/{user_id}",
         status_code=303
     )