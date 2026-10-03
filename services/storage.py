import base64
import secrets
from fastapi import HTTPException
from starlette.concurrency import run_in_threadpool
import asyncio
import aiofiles.os
import pathlib
from io import BytesIO
from PIL import Image

from repositories.forum import ForumRepository

class StorageService:
    ALLOWED_EXT = {"png", "jpeg", "jpg", "gif", "webp"}

    allowed_content_type = [
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/avif"
    ]

    FORMAT_TO_EXT = {"PNG": "png", "JPEG": "jpg", "WEBP": "webp", "GIF": "gif"}
    MSGS_UPLOAD_DIR = f"static/uploads/msgs_imgs"
    MAX_POST_IMG_SIZE = 10 * 1024 * 1024
    
    @staticmethod
    def _write_file(path: str, content: bytes):
        with open(path, "wb") as f:
            f.write(content)

    @staticmethod
    def check_img_ext(data: bytes):
        try:
            with Image.open(BytesIO(data)) as img:
                img.verify()
                format = img.format

        except Exception:
            raise ValueError("Invalid img content type")

        ext = StorageService.FORMAT_TO_EXT.get(format)

        if ext is None:
            raise ValueError("Invalid img content type")

        return ext

    @staticmethod
    async def save_img_dm(imgs: str) -> list[str]:
        saved_paths = []

        for img_data in imgs:

            header, encoded = img_data.split(",", 1)

            ext = header.split("/")[1].split(";")[0]

            if ext not in StorageService.ALLOWED_EXT:
                raise ValueError(f"Invalid image content type: {ext}")

            try:
                file_bytes = base64.b64decode(encoded)
            except Exception as e:
                raise ValueError(f"Unable to decode base64: {e}")

            unique_name = f"{secrets.token_hex(16)}.{ext}"  

            file_path = f"{StorageService.MSGS_UPLOAD_DIR}/{unique_name}"

            await run_in_threadpool(StorageService._write_file, file_path, file_bytes)

            saved_paths.append(f"/{file_path}")

        return saved_paths

    @staticmethod
    async def save_imgs_post(imgs: list):
        if len(imgs) > 5:
            raise HTTPException(
                status_code=403,
                detail="you can't choose more than 5 pictures"
            )
        
        fullpaths = []

        for img in imgs:
            if not img or img.size == 0:
                print("img size is less than 0")
                continue
            
            content = await img.read()

            if len(content) > StorageService.MAX_POST_IMG_SIZE + 1:
                raise HTTPException(
                    status_code=413,
                    detail=f"too large file. max file size is {StorageService.MAX_POST_IMG_SIZE} MiB"
                )

            ext = await run_in_threadpool(StorageService.check_img_ext, content)

            if ext:
                unique_name = secrets.token_hex(16)
                fullpath = f"static/uploads/post_imgs/{unique_name}.{ext}"
                await run_in_threadpool(lambda p=fullpath, c=content: open(p, "wb").write(c))
                fullpaths.append(fullpath)
    
        return fullpaths

    @staticmethod
    async def delete_post_imgs(imgs: list, db):
        for img in imgs:

            path = img.path[1:]

            try:
                await aiofiles.os.remove(path)
            except FileNotFoundError:
                print(f"{path}: NOT FOUND")
            except PermissionError:
                print(f"{path}: NO PERMISSION")
        



