from django.urls import re_path, path
from . import consumers
from . import video_consumer

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<consultation_id>\w+)/$', consumers.ChatConsumer.as_asgi()),
    path('ws/video/<int:consultation_id>/', video_consumer.VideoSignalConsumer.as_asgi()),
]
