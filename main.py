import asyncio
import logging

from fastapi import FastAPI, Depends, WebSocket
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from core.redis_conf import redis
from core.redis.pubsub import PubSub
from repositories.admin_forum import AdminForumRepository
from repositories.chatbox import CBMSGSRepository
from repositories.notifications import NotificationsRepository
from security.auth import get_current_user, get_current_user_ws
from database.database import get_db, SessionLocal, engine
from services.chatbox_service import CBService
from services.forum import ForumService
from templates.template_config import template
from templates.filters import last_seen
from services.gpt import GPTService
from dependencies.dependencies import get_gpt_service

from routers.auth_api import router as auth
from routers.profile_api import router as profile
from routers.account_api import router as account
from routers.sub_buy_api import router as buy
from routers.dms import router as dms
from routers.admin_api import router as admin
from routers.forum import router as forum
from routers.users import router as user

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

async def sync_views_loop():
        while True:
            async with SessionLocal() as db:
                await ForumService.sync_views(db)
            await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):

    await redis.ping()

    pubsub = PubSub()

    sync_task = asyncio.create_task(
        sync_views_loop()
    )

    listener_task = asyncio.create_task(
        pubsub.listen()
    )
    
    try:
        yield

    finally:

        sync_task.cancel()
        listener_task.cancel()

        await asyncio.gather(
            sync_task,
            listener_task,
            return_exceptions=True
        )

        await redis.close()

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth)
app.include_router(profile)
app.include_router(account)
app.include_router(dms)
app.include_router(buy)
app.include_router(admin)
app.include_router(forum)
app.include_router(user)

@app.get("/")
async def index(request: Request, current_user = Depends(get_current_user), db = Depends(get_db)):
    token = request.cookies.get("token")

    if token:
        unread = await NotificationsRepository.get_all(current_user.id, db)
        
        template.env.globals["unread_notifications"] = unread

        messages = await CBMSGSRepository.get(db)

        categories = await AdminForumRepository.get_all_categories(db)
        subcategories = await AdminForumRepository.get_all_subcats(db)

        return template.TemplateResponse(
            request=request,
            name="index.html",
            context={"user": current_user, "msgs": messages, "cats": categories, "subcats": subcategories}
        )
    else:
        return template.TemplateResponse(
            request=request,
            name="index_un.html"
        )

@app.websocket("/ws")
async def ws(websocket: WebSocket, current_user = Depends(get_current_user_ws)):
    current_user_id = current_user.id
    current_user_name = current_user.name

    message = await CBService.ws(websocket, current_user_id, current_user_name)
