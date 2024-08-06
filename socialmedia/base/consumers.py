from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from base.models import User
import json

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.group_name = 'notifications'
        try:
            self.user = await sync_to_async(User.objects.get)(id=self.user_id)
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()
        except User.DoesNotExist:
            # await self.send(text_data=json.dumps({
            #     'error': 'User not found'
            # }))
            await self.close()

        # if not User.objects.filter(id=self.user_id).exists():
        #     await self.close()
        #     return

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def send_notification(self, event):
        message = event['message']
        exclude = event.get('exclude', [])

        if self.user_id not in exclude:
            await self.send(text_data=json.dumps({
                'message': message
            }))
