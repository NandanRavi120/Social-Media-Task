from channels.generic.websocket import AsyncWebsocketConsumer
import json
from channels.db import database_sync_to_async
from base.models import User


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.group_name = f"User_{self.user_id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def send_notification(self, event):
        message = event['message']
        exclude = event.get('exclude', [])

        if await database_sync_to_async(User.objects.filter(id=self.user_id).exists)():
            if self.user_id not in exclude:
                await self.send(text_data=json.dumps({
                    'message': message
                }))



