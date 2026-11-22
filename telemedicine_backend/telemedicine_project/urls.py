from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
# from drf_yasg.views import get_schema_view
# from drf_yasg import openapi
# from rest_framework.permissions import AllowAny
from .views import api_home, api_info

# schema_view = get_schema_view(
#     openapi.Info(
#         title="Telemedicine API",
#         default_version="v1",
#         description="API documentation for the Telemedicine application",
#         terms_of_service="https://www.google.com/policies/terms/",
#         contact=openapi.Contact(email="support@example.com"),
#         license=openapi.License(name="BSD License"),
#     ),
#     public=True,
#     permission_classes=(AllowAny,),
# )

urlpatterns = [
    path("", api_home, name="api-home"),  # Root URL - API home page
    path("api/info/", api_info, name="api-info"),  # JSON API info endpoint
    path("admin/", admin.site.urls),
    path("users/", include("users.urls")),
    path("consultations/", include("consultations.urls")),
    path("marketing/", include("marketing.urls")),

    # Swagger URLs - Temporarily disabled
    # path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    # path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]

# ✅ Serve Media Files During Development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
