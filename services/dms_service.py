import json
from fastapi import WebSocket, WebSocketException, WebSocketDisconnect, Depends
import asyncio

from core.redis_conf import redis
from database.database import get_db, SessionLocal, engine
from models.messages import Messages
from repositories.messages import MsgRepository
from security.auth import get_current_user_ws
from websocket.manager import manager
from services.storage import StorageService
from dependencies.dependencies import get_gpt_service
from services.gpt import GPTService

async def ai_bg(prompt, recipient_id, current_user, gpt_service: GPTService):
    try:
        async with SessionLocal() as db:
            history = await MsgRepository.get_messages(current_user, recipient_id, db, 10)

        messages = []

        for m in history:
            role = "assistant" if m.sender_id == recipient_id else "user"
            messages.append({"role": role, "content": m.msg})

        response = await gpt_service.generate_text_response(prompt, messages)

        if response["failure"]:
            print("AI FAILED")

        async with SessionLocal() as db:
            await MsgRepository.create(11, current_user.id, response["response"], db)

        result = await redis.publish(
            f"chat:user:{recipient_id}",
            json.dumps({
            "type": "dm_msg",
            "sender_id": recipient_id,
            "recipient_id": current_user.id,
                "msg": response["response"],
                "imgs": None
            })
        )
        
        print("PUBLISHED", result)
    except Exception as e:
        print(f"ai_bg failed: {e}")
    

class DMsServices:
    @staticmethod
    async def ws(websocket: WebSocket, current_user):
        await websocket.accept()
        await manager.dm_connect(current_user.id, websocket)

        try:
            while True:
                data = await websocket.receive_json()

                recipient_id = data["recipient_id"]
                msg = data["msg"]
                imgs = data["imgs"]

                async with SessionLocal() as db:
                    message = await MsgRepository.create(sender_id=current_user.id, recipient_id=recipient_id, msg=msg, db=db)

                try:
                    imgs_paths = await StorageService.save_img_dm(imgs)
                except ValueError:
                    continue

                async with SessionLocal() as db:
                    await MsgRepository.add_imgs(message.id, imgs_paths, db)

                if message is None:
                    continue

                result = await redis.publish(
                    f"chat:user:{recipient_id}",
                    json.dumps({
                        "type": "dm_msg",
                        "sender_id": current_user.id,
                        "recipient_id": recipient_id,
                        "msg": msg,
                        "imgs": imgs_paths
                    })
                )

                print("PUBLISHED", result)
                # await manager.send_dm(
                #     current_user.id,
                #     recipient_id,
                #     msg
                # )
        except WebSocketDisconnect:
            pass
        except Exception as e:
            print(f"DB ERROR: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print(
                "WS CLOSED:",
                current_user.id,
                engine.pool.status()
            )
            await manager.dm_disconnect(current_user.id, websocket)

    @staticmethod
    async def ai_ws(websocket: WebSocket, current_user, gpt_service: GPTService = Depends(get_gpt_service)):
        await websocket.accept()
        await manager.dm_connect(current_user.id, websocket)
        
        try:
            while True:
                data = await websocket.receive_json()
        
                recipient_id = data["recipient_id"]
                msg = data["msg"]

                async with SessionLocal() as db:
                    message = await MsgRepository.create(sender_id=current_user.id, recipient_id=recipient_id, msg=msg, db=db)

                if message is None:
                    continue

                asyncio.create_task(ai_bg(msg, recipient_id, current_user, gpt_service))

        except WebSocketDisconnect:
            pass
        except Exception as e:
            print(f"DB ERROR: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print(
                "WS CLOSED:",
                current_user.id,
                engine.pool.status()
            )
            await manager.dm_disconnect(current_user.id, websocket)

