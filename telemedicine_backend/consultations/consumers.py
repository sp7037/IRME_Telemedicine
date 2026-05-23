import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import ConsultationChat, Consultation
from users.models import User
from asgiref.sync import sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.consultation_id = self.scope['url_route']['kwargs']['consultation_id']
        self.room_group_name = f'consultation_{self.consultation_id}'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        sender_id = data['sender_id']

        # Store message in DB
        consultation = await sync_to_async(Consultation.objects.get)(id=self.consultation_id)
        sender = await sync_to_async(User.objects.get)(id=sender_id)
        chat = await sync_to_async(ConsultationChat.objects.create)(consultation=consultation, sender=sender, message=message)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender.email,
                'timestamp': chat.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))
