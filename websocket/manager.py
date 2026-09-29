from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

from core.redis_conf import redis
from database.database import SessionLocal
from repositories.forum import ForumRepository
from repositories.users import UsersRepository
from services.users import UsersService


class ConnectionManager:
    def __init__(self):
        self.connections: dict[int, set[WebSocket]] = {}
        self.page_connections: dict[int, set[WebSocket]] = {}
        self.cb_connections: set[WebSocket] = set()
        self.post_connections: dict[int, set[WebSocket]] = {}
        self.dm_connections: dict[int, set[WebSocket]] = {}

    async def _safe_send(self, socket: WebSocket, data: dict) -> bool:
        try:
            await asyncio.wait_for(socket.send_json(data), timeout=5)
            return True
        except Exception as e:
            print(f"send failed: {e}")
            return False

    async def connect(self, user_id: int, ws: WebSocket):
        if user_id not in self.connections:
            self.connections[user_id] = set()
        self.connections[user_id].add(ws)
        await redis.sadd("online_users", user_id)
        print(f"[ websocket ]: info: sending status: {user_id}, online")
        await manager.send_user_status("user_status", user_id, "online")

        count = await redis.scard("online_users")

        await manager.broadcast_online_users(count)

        print(f"[ websocket ]: info: connected new user to main ws with id {user_id}")

    async def user_page_connect(self, user_id, ws: WebSocket):
        if user_id not in self.page_connections:
            self.page_connections[user_id] = set()
        self.page_connections[user_id].add(ws)

    async def cb_connect(self, ws: WebSocket):
        self.cb_connections.add(ws)
        print(f"[ websocket ]: info: new chatbox connection")

    async def post_connect(self, post_id, ws: WebSocket):
        if post_id not in self.post_connections:
            self.post_connections[post_id] = set()

        self.post_connections[post_id].add(ws)
        print(f"[ websocket ]: info: connected new post to post ws with id {post_id}")

    async def disconnect(self, user_id: int, ws: WebSocket):
        if user_id in self.connections:
            self.connections[user_id].discard(ws)

            if not self.connections[user_id]:
                async with SessionLocal() as db:
                    try:
                        await UsersService.set_online(str(datetime.now().replace(microsecond=0)), user_id, db)
                    except Exception:
                        print("an error has occurred")
                        await db.rollback()
                        raise

                del self.connections[user_id]
                await redis.srem("online_users", user_id)
                print(f"[ websocket ]: info: sending status: {user_id}, offline")
                await manager.send_user_status("user_status", user_id, "offline")

                count = await redis.scard("online_users")

                await manager.broadcast_online_users(count)

        print(f"[ websocket ]: info: disconnected from main ws new user with id {user_id}")

    async def user_page_disconnect(self, user_id, ws: WebSocket):
        if user_id in self.page_connections:
            self.page_connections[user_id].discard(ws)

            if not self.page_connections[user_id]:
                del self.page_connections[user_id]

    async def cb_disconnect(self, ws: WebSocket):
        self.cb_connections.discard(ws)
        print(f"[ websocket ]: info: chatbox disconnect")

    async def post_disconnect(self, post_id: int, ws: WebSocket):
        if post_id in self.post_connections:
            self.post_connections[post_id].discard(ws)

            if not self.post_connections[post_id]:
                del self.post_connections[post_id]

    async def dm_connect(self, user_id: int, ws: WebSocket):
        if user_id not in self.dm_connections:
            self.dm_connections[user_id] = set()

        self.dm_connections[user_id].add(ws)

        print(f"[ websocket ]: info: connected to dm ws new user with id {user_id}")


    async def dm_disconnect(self, user_id: int, ws: WebSocket):
        if user_id in self.dm_connections:
            self.dm_connections[user_id].discard(ws)

            if not self.dm_connections[user_id]:
                del self.dm_connections[user_id]

        print(f"[ websocket ]: info: disconnected from dm ws new user with id {user_id}")

    async def send_dm(self, msg_type: str, sender_id: int, recipient_id: int, msg: str | None = None, imgs: list | None = None, istyping: bool | None = None, client_id: str | None = None):
        print(
            "SEND_DM:",
            recipient_id,
            "connections:",
            self.dm_connections
        )

        if recipient_id not in self.dm_connections:
            return

        for socket in list(self.dm_connections[recipient_id]):
            try:
                print("SENDING DM:", {
                    "type": "dm_msg",
                    "sender_id": sender_id,
                    "msg": msg
                })

                await socket.send_json({
                    "type": "dm_msg",
                    "client_id": client_id,
                    "msg_type": msg_type,
                    "sender_id": sender_id,
                    "recipient_id": recipient_id,
                    "msg": msg,
                    "istyping": istyping,
                    "imgs": imgs
                })
            except Exception as e:
                await self.dm_disconnect(user_id=recipient_id, ws=socket)
                print(f"DB ERROR: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()

    async def send_cbm(self, sender_id: int, sender_name: str, msg: str):
        for socket in list(self.cb_connections):
            try:
                await socket.send_json({
                    "type": "cbm",
                    "sender_id": sender_id,
                    "sender_name": sender_name,
                    "msg": msg
                })
            except Exception as e:
                print(f"error: {e}")
                await self.cb_disconnect(socket)

    async def notify(self, user_id: int, notif: dict):
        if user_id not in self.connections:
            print(f"user {user_id} not in connections — offline")
            return

        for socket in list(self.connections[user_id]):
            try:
                await self._safe_send(socket, {
                    "type": "notification",
                    **notif
                })
                print(f"sent to {user_id}")
            except Exception as e:
                print(f"error: {e}")
                await self.disconnect(user_id, socket)

    async def post_updates(self, post_id: int, data: dict):
        if post_id not in self.post_connections:
            return

        for socket in list(self.post_connections[post_id]):
            try:
                await socket.send_json(data)
            except Exception as e:
                print(f"error: {e}")
                await self.post_disconnect(post_id, socket)

    async def send_user_status(self, type: str, user_id: int, status: str):
        data = {"type": type, "user_id": user_id, "status": status}

        for sockets in self.page_connections.values():
            for socket in list(sockets):
                try:
                    print("sending to ws")
                    await socket.send_json(data)
                except Exception as e:
                    print(f"error: {e}")
                    await self.user_page_disconnect(user_id, socket)

    async def broadcast_online_users(self, value: int):
        for user_id, sockets in list(self.connections.items()):
            for socket in list(sockets):
                ok = await self._safe_send(socket, {
                    "type": "current_online",
                    "value": value
                })

                if not ok:
                    await self.disconnect(user_id, socket)



manager = ConnectionManager()