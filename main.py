import asyncio

from fastapi import FastAPI, Depends, WebSocket
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager

from core.redis_conf import redis
from repositories.admin_forum import AdminForumRepository
from repositories.chatbox import CBMSGSRepository
from security.auth import get_current_user, get_current_user_ws
from database.database import get_db, SessionLocal
from services.chatbox_service import CBService
from services.forum import ForumService
from templates.template_config import template
from templates.filters import last_seen

from routers.auth_api import router as auth
from routers.profile_api import router as profile
from routers.account_api import router as account
from routers.sub_buy_api import router as buy
from routers.dms import router as dms
from routers.admin_api import router as admin
from routers.forum import router as forum
from routers.users import router as user


async def sync_views_loop():
        while True:
            async with SessionLocal() as db:
                await ForumService.sync_views(db)
                print("views synced with db")
            await asyncio.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI, db = Depends(get_db)):
    await redis.ping()
    print("Redis connected")

    task = asyncio.create_task(sync_views_loop())

    yield

    task.cancel()
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
async def ws(websocket: WebSocket, current_user = Depends(get_current_user_ws), db = Depends(get_db)):
    message = await CBService.ws(websocket, current_user, db)