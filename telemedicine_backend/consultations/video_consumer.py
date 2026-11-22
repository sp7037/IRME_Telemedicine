import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Consultation
from .video import get_or_create_video_join

logger = logging.getLogger(__name__)

class VideoSignalConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.consultation_id = self.scope['url_route']['kwargs']['consultation_id']
        self.user = self.scope['user']
        self.room_group_name = f'video_signal_{self.consultation_id}'
        
        # Verify user is part of this consultation
        if not await self.is_user_authorized():
            await self.close()
            return
        
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        
        # Send initial video room credentials
        await self.send_room_credentials()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
    
    async def receive(self, text_data):
        """Handle WebRTC signaling messages"""
        try:
            data = json.loads(text_data)
            signal_type = data.get('type')
            
            if signal_type == 'offer':
                # Forward offer to other participants
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'webrtc_signal',
                        'signal': 'offer',
                        'data': data['data'],
                        'from_user': self.user.id
                    }
                )
            elif signal_type == 'answer':
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'webrtc_signal',
                        'signal': 'answer',
                        'data': data['data'],
                        'from_user': self.user.id
                    }
                )
            elif signal_type == 'ice_candidate':
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'webrtc_signal',
                        'signal': 'ice_candidate',
                        'data': data['data'],
                        'from_user': self.user.id
                    }
                )
        except Exception as e:
            logger.error(f"Video signal error: {e}")
    
    async def webrtc_signal(self, event):
        """Send WebRTC signal to specific client"""
        # Don't send signal back to sender
        if event['from_user'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': event['signal'],
                'data': event['data']
            }))
    
    async def send_room_credentials(self):
        """Send video room credentials to client"""
        try:
            consultation = await self.get_consultation()
            credentials = await database_sync_to_async(get_or_create_video_join)(
                consultation, self.user
            )
            await self.send(text_data=json.dumps({
                'type': 'room_ready',
                'credentials': credentials
            }))
        except Exception as e:
            logger.error(f"Failed to send room credentials: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    @database_sync_to_async
    def is_user_authorized(self):
        try:
            consultation = Consultation.objects.get(id=self.consultation_id)
            return self.user.is_authenticated and (
                consultation.patient.user == self.user or
                consultation.doctor.user == self.user or
                consultation.tmc.user == self.user
            )
        except Consultation.DoesNotExist:
            return False
    
    @database_sync_to_async
    def get_consultation(self):
        return Consultation.objects.get(id=self.consultation_id)
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Consultation
from .video import get_or_create_video_join

logger = logging.getLogger(__name__)

class VideoSignalConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.consultation_id = self.scope['url_route']['kwargs']['consultation_id']
        self.user = self.scope['user']
        self.room_group_name = f'video_signal_{self.consultation_id}'
        
        # Verify user is part of this consultation
        if not await self.is_user_authorized():
            await self.close()
            return
        
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        
        # Send initial video room credentials
        await self.send_room_credentials()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
    
    async def receive(self, text_data):
        """Handle WebRTC signaling messages"""
        try:
            data = json.loads(text_data)
            signal_type = data.get('type')
            
            if signal_type == 'offer':
                # Forward offer to other participants
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'webrtc_signal',
                        'signal': 'offer',
                        'data': data['data'],
                        'from_user': self.user.id
                    }
                )
            elif signal_type == 'answer':
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'webrtc_signal',
                        'signal': 'answer',
                        'data': data['data'],
                        'from_user': self.user.id
                    }
                )
            elif signal_type == 'ice_candidate':
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'webrtc_signal',
                        'signal': 'ice_candidate',
                        'data': data['data'],
                        'from_user': self.user.id
                    }
                )
        except Exception as e:
            logger.error(f"Video signal error: {e}")
    
    async def webrtc_signal(self, event):
        """Send WebRTC signal to specific client"""
        # Don't send signal back to sender
        if event['from_user'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': event['signal'],
                'data': event['data']
            }))
    
    async def send_room_credentials(self):
        """Send video room credentials to client"""
        try:
            consultation = await self.get_consultation()
            credentials = await database_sync_to_async(get_or_create_video_join)(
                consultation, self.user
            )
            await self.send(text_data=json.dumps({
                'type': 'room_ready',
                'credentials': credentials
            }))
        except Exception as e:
            logger.error(f"Failed to send room credentials: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    @database_sync_to_async
    def is_user_authorized(self):
        try:
            consultation = Consultation.objects.get(id=self.consultation_id)
            return self.user.is_authenticated and (
                consultation.patient.user == self.user or
                consultation.doctor.user == self.user or
                consultation.tmc.user == self.user
            )
        except Consultation.DoesNotExist:
            return False
    
    @database_sync_to_async
    def get_consultation(self):
        return Consultation.objects.get(id=self.consultation_id)
