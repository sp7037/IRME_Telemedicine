from django.urls import re_path
from consultations.consumers import ChatConsumer

websocket_urlpatterns = [
    re_path(r'ws/consultations/(?P<consultation_id>\d+)/$', ChatConsumer.as_asgi()),
]
