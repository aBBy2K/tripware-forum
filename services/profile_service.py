import secrets
from fastapi import UploadFile, File
from passlib.hash import bcrypt
from starlette.concurrency import run_in_threadpool
from schemas.users import UsersEdit

def _write_file(path: str, content: bytes):
    with open(path, "wb") as f:
        f.write(content)


class ProfileService:
    @staticmethod
    async def edit(db, current_user, name: str, pfp: UploadFile = File()):
        has_pfp = pfp and pfp.size > 0

        allowed_content_type = [
            "image/jpeg",
            "image/png",
            "image/webp",
            "image/avif"
        ]

        try:
            u = UsersEdit(name=name or None, pfp=pfp)
        except Exception as e:
            return {
                "success": False,
                "message": f"Couldn't update profile : {e}"
            }

        data = u.model_dump(exclude_none=True, exclude={"pfp"})
        if not data and not has_pfp:
            return {
                "success": False,
                "message": "No valid fields were provided"
            }
        if has_pfp:
            if pfp.content_type not in allowed_content_type:
                return {
                    "success": False,
                    "message": "Invalid picture content type"
                }

            ext = pfp.filename.split(".")[-1]
            unique_name = secrets.token_hex(16)
            save_path = f"static/uploads/pfps/{unique_name}.{ext}"

            content = await pfp.read()

            await run_in_threadpool(_write_file, save_path, content)

            current_user.pfp = f"/{save_path}"

        for k,v in data.items():
            setattr(current_user, k, v)

        await db.commit()


        return {
            "success": True,
            "message": "Profile successfully updated"
        }