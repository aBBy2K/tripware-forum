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
from services.notifications import NotificationsService

async def ai_bg(prompt, client_id, recipient_id, current_user, gpt_service: GPTService):
    try:
        await redis.publish(
            f"chat:user:{recipient_id}",
            json.dumps({
                "type": "dm_msg",
                "msg_type": "sys",
                "sender_id": current_user.id,
                "recipient_id": recipient_id,
                "msg": "typing...",
                "istyping": True,
                "imgs": None
            }))

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
            await MsgRepository.create(11, client_id, current_user.id, response["response"], db)


        result = await redis.publish(
            f"chat:user:{recipient_id}",
            json.dumps({
                "type": "dm_msg",
                "msg_type": "user",
                "sender_id": recipient_id,
                "recipient_id": current_user.id,
                "msg": response["response"],
                "istyping": None,
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

                type = data["type"]
                recipient_id = data["recipient_id"]
                msg = data["msg"]

                if type == "sys":
                    istyping = data["istyping"]

                    result = await redis.publish(
                        f"chat:user:{recipient_id}",
                        json.dumps({
                            "type": "dm_msg",
                            "client_id": None,
                            "msg_type": "sys",
                            "sender_id": current_user.id,
                            "recipient_id": recipient_id,
                            "msg": msg,
                            "istyping": istyping,
                            "imgs": None
                        }))
                    
                elif type == "user":
                    imgs = data["imgs"]
                    client_id = data["client_id"]

                    if len(imgs) > 5:
                        async with SessionLocal() as db:
                            await NotificationsService.add_notif(
                                n_type="notification",
                                head="Too many pictures",
                                body="You can add up to 5 pictures per message",
                                is_read=True,
                                user_id=current_user.id,
                                db=db
                            )
                        continue

                    async with SessionLocal() as db:
                        message = await MsgRepository.create(sender_id=current_user.id, client_id=client_id, recipient_id=recipient_id, msg=msg, db=db)

                    try:
                        imgs_paths = await StorageService.save_img_dm(imgs)
                    except ValueError:
                        continue

                    try:
                        async with SessionLocal() as db:
                            await MsgRepository.add_imgs(message.id, imgs_paths, db)
                    except Exception:
                        continue

                    if message is None:
                        continue

                    result = await redis.publish(
                        f"chat:user:{recipient_id}",
                        json.dumps({
                            "type": "dm_msg",
                            "client_id": client_id,
                            "msg_type": "user",
                            "sender_id": current_user.id,
                            "recipient_id": recipient_id,
                            "msg": msg,
                            "istyping": None,
                            "imgs": imgs_paths
                        })
                    )
                    async with SessionLocal() as db:
                        await NotificationsService.add_notif(
                            n_type="notification",
                            head="New direct message",
                            body=f"You got new direct message: '{msg}' from {current_user.name}",
                            is_read=True,
                            user_id=recipient_id,
                            db=db
                        )

                    print("PUBLISHED", result)
                    # await manager.send_dm(
                    #     current_user.id,
                    #     recipient_id,
                    #     msg
                    # )
                elif type == "delete":
                    client_id = data["client_id"]

                    async with SessionLocal() as db:
                        await MsgRepository.delete(client_id, current_user.id, db)

                    result = await redis.publish(
                        f"chat:user:{recipient_id}",
                        json.dumps({
                        "type": "dm_msg",
                        "client_id": client_id,
                        "msg_type": "delete",
                        "sender_id": current_user.id,
                        "recipient_id": recipient_id,
                        "msg": None,
                        "istyping": None,
                        "imgs": None
                    })
                )
                    

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

                client_id = data["client_id"]
                recipient_id = data["recipient_id"]
                msg = data["msg"]
                type = data["type"]

                if type != "user":
                    continue

                async with SessionLocal() as db:
                    message = await MsgRepository.create(client_id=client_id, sender_id=current_user.id, recipient_id=recipient_id, msg=msg, db=db)

                if message is None:
                    continue

                asyncio.create_task(ai_bg(msg, client_id, recipient_id, current_user, gpt_service))

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

