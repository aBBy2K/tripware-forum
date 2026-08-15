from fastapi import WebSocket, WebSocketException, WebSocketDisconnect, Depends

from database.database import get_db, SessionLocal, engine
from models.messages import Messages
from repositories.messages import MsgRepository
from security.auth import get_current_user_ws
from websocket.manager import manager

class DMsServices:
    @staticmethod
    async def ws(websocket: WebSocket, current_user):
        await websocket.accept()
        await manager.connect(current_user.id, websocket)

        try:
            while True:
                data = await websocket.receive_json()

                recipient_id = data["recipient_id"]
                msg = data["msg"]

                async with SessionLocal() as db:
                    message = await MsgRepository.create(sender_id=current_user.id, recipient_id=recipient_id, msg=msg, db=db)

                if message is None:
                    continue

                await manager.send_dm(
                    current_user.id,
                    recipient_id,
                    msg
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
            await manager.disconnect(current_user.id, websocket)

