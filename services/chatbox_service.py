from fastapi import WebSocket, WebSocketDisconnect
from repositories.chatbox import CBMSGSRepository
from websocket.manager import manager

class CBService:
    @staticmethod
    async def ws(websocket: WebSocket, current_user, db):
        await websocket.accept()
        await manager.cb_connect(websocket)

        try:
            while True:
                data = await websocket.receive_json()

                msg = data["msg"]
    
                message = await CBMSGSRepository.create(current_user.id, msg, db)

                if message is None:
                    continue

                await manager.send_cbm(current_user.id, current_user.name, msg)
        except WebSocketDisconnect:
            pass
        except Exception as e:
            print(f"an internal error has occurred while trying to send message to db: {e}")
        finally:
            await manager.cb_disconnect(websocket)