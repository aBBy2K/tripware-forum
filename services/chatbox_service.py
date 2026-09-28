import json

from fastapi import WebSocket, WebSocketDisconnect

from core.redis_conf import redis
from database.database import SessionLocal, engine
from repositories.chatbox import CBMSGSRepository
from websocket.manager import manager

class CBService:
    @staticmethod
    async def ws(websocket: WebSocket, current_user_id, current_user_name):
        await websocket.accept()
        await manager.cb_connect(websocket)

        try:
            while True:
                data = await websocket.receive_json()

                msg = data["msg"]
                print("POOL: ", engine.pool.status())
                async with SessionLocal() as db:
                    message = await CBMSGSRepository.create(current_user_id, msg, db)
                print("POOL: ", engine.pool.status())
                if message is None:
                    continue

                await redis.publish(
                    f"cb:user",
                    json.dumps({
                        "type": "cbm",
                        "sender_id": current_user_id,
                        "sender_name": current_user_name,
                        "msg": msg
                    })
                )

                # await manager.send_cbm(current_user.id, current_user.name, msg)
        except WebSocketDisconnect:
            pass
        finally:
            await manager.cb_disconnect(websocket)