import json

from core.redis_conf import redis
from websocket.manager import manager


class PubSub:
    def __init__(self):
        self.redis = redis
        self.manager = manager


    async def listen(self):
        pubsub = self.redis.pubsub()

        await pubsub.psubscribe(
            "chat:user:*",
            "cb:user",
            "notification:user:*",
            "post:*"
        )

        async for msg in pubsub.listen():
            if msg["type"] != "pmessage":
                continue

            data = json.loads(msg["data"])

            if data["type"] == "dm_msg":
                await self.manager.send_dm(
                    sender_id=data["sender_id"],
                    recipient_id=data["recipient_id"],
                    msg=data["msg"]
                )

            if data["type"] == "cbm":
                await self.manager.send_cbm(
                    sender_id=data["sender_id"],
                    sender_name=data["sender_name"],
                    msg=data["msg"]
                )

            if data["type"] == "notification":
                await self.manager.notify(
                    user_id=data["user_id"],
                    notif=data["notif"]
                )

            if data["type"] == "new_comment" or data["type"] == "like" or data["type"] == "unlike":
                await self.manager.post_updates(
                    post_id=data["post_id"],
                    data=data["data"]
                )