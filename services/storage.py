import base64
import secrets
from starlette.concurrency import run_in_threadpool

class StorageService:
    ALLOWED_EXT = {"png", "jpeg", "jpg", "gif", "webp"}
    MSGS_UPLOAD_DIR = f"static/uploads/msgs_imgs"
    
    @staticmethod
    def _write_file(path: str, content: bytes):
        with open(path, "wb") as f:
            f.write(content)

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