import json

from core.redis_conf import redis
from websocket.manager import manager


class PubSub:

    def __init__(self):
        self.redis = redis
        self.manager = manager
        self.pubsub = None

    async def listen(self):
        self.pubsub = self.redis.pubsub()

        await self.pubsub.psubscribe(
            "chat:user:*",
            "cb:user",
            "notification:user:*",
            "post:*"
        )

        print("PUBSUB SUBSCRIBED")

        try:
            async for msg in self.pubsub.listen():

                if msg["type"] != "pmessage":
                    continue

                try:
                    data = json.loads(msg["data"])

                    if data["type"] == "dm_msg":
                        await self.manager.send_dm(
                            sender_id=data["sender_id"],
                            recipient_id=data["recipient_id"],
                            msg=data["msg"]
                        )

                    elif data["type"] == "cbm":
                        await self.manager.send_cbm(
                            sender_id=data["sender_id"],
                            sender_name=data["sender_name"],
                            msg=data["msg"]
                        )

                    elif data["type"] == "notification":
                        await self.manager.notify(
                            user_id=data["notif"]["user_id"],
                            notif=data["notif"]
                        )

                    elif data["type"] in (
                        "new_comment",
                        "like",
                        "unlike"
                    ):
                        await self.manager.post_updates(
                            post_id=data["post_id"],
                            data=data["data"]
                        )

                except Exception as e:
                    print("PUBSUB EVENT ERROR:", repr(e))

        finally:
            if self.pubsub:
                await self.pubsub.close()
                print("PUBSUB CLOSED")