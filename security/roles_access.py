from fastapi import Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.requests import Request

from database.database import get_db
from repositories.admin_forum import AdminForumRepository
from security.auth import get_current_user
from templates.template_config import template

user_allowed = ["User", "Premium", "Admin"]
premium_allowed = ["Premium", "Admin"]
admin_allowed = ["Admin"]

def require_user(request: Request, current_user = Depends(get_current_user)):
    token = request.cookies.get("token")
    if not token or current_user.role.name not in user_allowed:
        raise HTTPException(
            status_code=403,
            detail="no permission"
        )
    return current_user

def require_premium(request: Request, current_user = Depends(get_current_user)):
    token = request.cookies.get("token")
    if not token or current_user.role.name not in premium_allowed:
        raise HTTPException(
            status_code=403,
            detail="no permission"
        )
    return current_user

def require_admin(request: Request, current_user = Depends(get_current_user)):
    token = request.cookies.get("token")
    if not token or current_user.role.name not in admin_allowed:
        raise HTTPException(
            status_code=403,
            detail="no permission"
        )
    return current_user

def can_post(subcat, current_user) -> bool:
    if subcat.required_role is None:
        return True
    if current_user.role.name == "Admin":
        return True
    return current_user.role.name == subcat.required_role
