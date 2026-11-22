from django.urls import path
from users.views.authentication import (
    LoginAPIView,
    LogoutAPIView,
    RefreshTokenAPIView,
    RegisterAPIView,
    ResendRegistrationEmailOTPAPIView,
    VerifyRegistrationEmailAPIView,
)
from users.views.profiles import (
    UserProfileAPIView,
    TMCPatientsAPIView,
    TMCProfileAPIView,
    TMCQualificationDocumentAPIView,
    TMCQualificationDocumentDetailAPIView,
)
from users.views.pincode_lookup import PincodeLookupAPIView

urlpatterns = [
    # -------------------------------------
    # Authentication Endpoints
    # -------------------------------------
    path("register/", RegisterAPIView.as_view(), name="user-register"),
    path("verify-email/", VerifyRegistrationEmailAPIView.as_view(), name="verify-registration-email"),
    path("verify-doctor-email/", VerifyRegistrationEmailAPIView.as_view(), name="verify-doctor-email"),
    path("resend-email-otp/", ResendRegistrationEmailOTPAPIView.as_view(), name="resend-email-otp"),
    path("resend-doctor-email-otp/", ResendRegistrationEmailOTPAPIView.as_view(), name="resend-doctor-email-otp"),
    path("login/", LoginAPIView.as_view(), name="user-login"),
    path("logout/", LogoutAPIView.as_view(), name="user-logout"),
    path("token/refresh/", RefreshTokenAPIView.as_view(), name="token-refresh"),

    # -------------------------------------
    # Profile Management Endpoints
    # -------------------------------------
    path("profile/", UserProfileAPIView.as_view(), name="user-profile"),
    path("tmc/profile/", TMCProfileAPIView.as_view(), name="tmc-profile"),
    path("tmc/qualification-documents/", TMCQualificationDocumentAPIView.as_view(), name="tmc-qualification-documents"),
    path("tmc/qualification-documents/<int:pk>/", TMCQualificationDocumentDetailAPIView.as_view(), name="tmc-qualification-document-detail"),
    path("patients/", TMCPatientsAPIView.as_view(), name="tmc-patients"),
    path("pincode-lookup/", PincodeLookupAPIView.as_view(), name="pincode-lookup"),
]
