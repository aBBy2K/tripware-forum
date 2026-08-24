import asyncio
import os
from typing import Annotated
from fastapi import Depends, APIRouter, Form, HTTPException, UploadFile, File
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import EmailStr

from core.redis_conf import redis
from database.database import get_db, engine
from models import Users
from repositories.admin_forum import AdminForumRepository
from security.auth import get_current_user
from security.roles_access import require_admin
from services.admin_forum import AdminForumService
from services.auth_service import AuthService
from services.profile_service import ProfileService
from templates.template_config import template

router = APIRouter(prefix="/admin", tags=["Admin panel"])

@router.get("/")
def admin_page(request: Request, admin = Depends(require_admin)):
    return template.TemplateResponse(
        request=request,
        name="admin/admin.html",
    )

@router.get("/ban")
def ban_page(request: Request, uid: int | None = None, admin = Depends(require_admin)):
    return template.TemplateResponse(
        request=request,
        name="admin/ban.html",
        context={"uid": uid}
    )

@router.post("/ban")
async def ban(request: Request, admin = Depends(require_admin), db = Depends(get_db), current_user = Depends(get_current_user), uid: int = Form(), reason: str = Form()):
    ban_unban = await AdminForumService.ban_unban(db, uid, reason)

    return template.TemplateResponse(
        request=request,
        name="admin/ban.html",
        context={"e": ban_unban["message"]}
    )

@router.get("/reports")
async def reports_page(request: Request, admin = Depends(require_admin), db = Depends(get_db)):
    reports = await AdminForumRepository.get_reports(db)

    return template.TemplateResponse(
        request=request,
        name="admin/reports.html",
        context={"reports": reports}
    )

@router.get("/c_create")
def create_category_page(request: Request, admin = Depends(require_admin)):
    return template.TemplateResponse(
        request=request,
        name="admin/c_create.html"
    )

@router.post("/c_create")
async def create_category(request: Request, name: str = Form(), vis: str = Form(), db = Depends(get_db), admin = Depends(require_admin)):
    category = await AdminForumService.add_cat(name, vis, db)
    return template.TemplateResponse(
        request=request,
        name="admin/c_create.html",
        context={"e": "Category created"}
    )

@router.get("/sc_create")
async def create_subcategory_page(request: Request, admin = Depends(require_admin), db = Depends(get_db)):
    categories = await AdminForumRepository.get_all_categories(db)

    return template.TemplateResponse(
        request=request,
        name="admin/sc_create.html",
        context={"cats": categories}
    )

@router.post("/sc_create")
async def create_category(request: Request, name: str = Form(), c_cat: str = Form(), role: str = Form(), db = Depends(get_db), admin = Depends(require_admin)):
    subcategory = await AdminForumService.add_subcat(name, c_cat, role, db)
    return template.TemplateResponse(
        request=request,
        name="admin/sc_create.html",
        context={"e": "subcategory created"}
    )

@router.get("/reports/{rid}/delete")
async def delete_report(request: Request, rid: int, db = Depends(get_db), current_user = Depends(get_current_user), admin = Depends(require_admin)):
    delete = await AdminForumRepository.delete_report(rid, db)
    return {"success": True, "message": "Deleted"}

@router.get("/flushredis")
async def flush_redis_cache(request: Request, current_user = Depends(get_current_user), admin = Depends(require_admin)):
    await redis.flushdb()
    print("cache is flushed")
    return {"success": True, "message": "flushed"}


@router.get("/pool")
async def pool():
    print(
        f"POOL REQUEST | PID={os.getpid()} | "
        f"{engine.pool.status()}",
        flush=True
    )

    return {
        "pid": os.getpid(),
        "pool": engine.pool.status()
    }

@router.get("/pool_test")
async def pool():
    print("BEFORE:", engine.pool.status())

    await asyncio.sleep(5)

    print("AFTER:", engine.pool.status())

    return {"ok": True}