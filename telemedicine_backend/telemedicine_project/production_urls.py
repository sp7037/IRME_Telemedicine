from django.urls import include, path, re_path
from .deployment_views import health, spa
from .protected_media import media

urlpatterns = [
    path("api/healthz/", health, name="healthz"),
    path("api/", include("telemedicine_project.urls")),
    path("media/<path:name>", media, name="protected-media"),
    re_path(r"^(?P<route>.*)$", spa, name="frontend-spa"),
]
