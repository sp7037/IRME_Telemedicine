from django.urls import path
from users.views.authentication import (
    LoginAPIView,
    LogoutAPIView,
    RefreshTokenAPIView,
    RegisterAPIView,
)
from users.views.profiles import UserProfileAPIView, TMCPatientsAPIView

urlpatterns = [
    # -------------------------------------
    # Authentication Endpoints
    # -------------------------------------
    path("register/", RegisterAPIView.as_view(), name="user-register"),
    path("login/", LoginAPIView.as_view(), name="user-login"),
    path("logout/", LogoutAPIView.as_view(), name="user-logout"),
    path("token/refresh/", RefreshTokenAPIView.as_view(), name="token-refresh"),

    # -------------------------------------
    # Profile Management Endpoints
    # -------------------------------------
    path("profile/", UserProfileAPIView.as_view(), name="user-profile"),
    path("patients/", TMCPatientsAPIView.as_view(), name="tmc-patients"),
]
