import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# ✅ Ensure Django settings are loaded before anything else
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'telemedicine_project.settings')
django.setup()  # ✅ Force Django to initialize before ASGI loads

# ✅ Import routing AFTER Django setup
import consultations.routing

# ✅ Define ASGI application
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            consultations.routing.websocket_urlpatterns
        )
    ),
})
