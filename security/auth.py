from datetime import datetime, timedelta
from fastapi import Depends, Request, HTTPException, WebSocket, WebSocketException, status
from fastapi.responses import RedirectResponse
from jose import jwt, JWTError
from sqlalchemy import select

from database.database import get_db
from models.users import Users
from repositories.users import UsersRepository
from config import DB_SECRET_KEY
from templates.template_config import template

SECRET_KEY = DB_SECRET_KEY
ALIVE = 30
ALGORITHM = "HS256"

class UserBanned:
    pass

def create_access_key(data: dict):
    to_encode = data.copy()

    alive_time = datetime.now() + timedelta(days=30)

    to_encode.update({"exp": alive_time})

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt

async def _get_user_from_token(token: str | None, db) -> Users | None:
    if not token:
        return
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        user_id = int(payload["sub"])
        user = await UsersRepository.get_by_id(db, user_id)

        return user
    except JWTError:
        return None

#http
async def get_current_user(request: Request, db = Depends(get_db)):
    token = request.cookies.get("token")

    if not token:
        if not str(request.url.path) == "/":
            raise HTTPException(
                status_code=403,
                detail="no permission"
            )

    user = await _get_user_from_token(token, db)
    if not user:
        return {
            "success": False
        }

    if user and user.is_banned:
        raise HTTPException(
            status_code=403,
            detail=f"Your account is banned. Reason: {user.ban_reason}"
        )

    return user

#ws
async def get_current_user_ws(websocket: WebSocket, db = Depends(get_db)):
    token = websocket.cookies.get("token")

    user = await _get_user_from_token(token, db)

    if not user:
       raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
   
    if user and user.is_banned:
       raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    return user