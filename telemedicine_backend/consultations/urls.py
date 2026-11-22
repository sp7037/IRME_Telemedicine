from django.urls import path
from .views import DirectBookingPreviewView
from .views import DoctorAvailabilityView, DoctorAvailabilityCreateView, DoctorResponseView, DoctorScheduleView, DoctorScheduleDetailView, AvailableDoctorsView,ConsultationBookingView, PatientResponseView
from .views import ConsultationHistoryView, DoctorPendingRequestsView
from .views import UpdateConsultationStatusView
from consultations.views import ConsultationChatHistoryView, SendMessageView
from consultations.views import PrescriptionView
from consultations.views import PrescriptionPDFView
from consultations.views import PrescriptionVersionsView
from consultations.staff_api import (
    StaffConsultationAuditView,
    StaffExportConsultationsCSVView,
    StaffExportDoctorEarningsCSVView,
    StaffExportPatientWalletCSVView,
    StaffExportSummaryCSVView,
    StaffExportTMCEntriesCSVView,
    StaffDoctorVerificationListView,
    StaffDoctorVerificationUpdateView,
    StaffAdminPlatformWalletTopupView,
    StaffOperationsReportView,
    StaffFeeSettingsView,
    StaffPatientListView,
    StaffPatientRechargeRequestListView,
    StaffPatientRechargeRequestProcessView,
    StaffPatientWalletTopupView,
    StaffTMCListView,
    StaffTMCRechargeRequestListView,
    StaffTMCRechargeRequestProcessView,
    StaffTMCWalletTopupView,
)
from consultations.views import DoctorProfileCompletionView
from consultations.views import DoctorQueuedConsultationsView, StartConsultationView, CompleteConsultationView, ActiveConsultationView
from consultations.views import (
    ConsultationEventsView,
    PatientFollowUpRequestView,
    DoctorFollowUpResponseView,
    TMCDashboardSummaryView,
    TMCConsultationListView,
    TMCBookConsultationView,
    PatientWalletSummaryView,
    PatientWalletRechargeOrderView,
    PatientWalletRechargeVerifyView,
    PatientWalletRechargeCancelView,
    DoctorEarningsSummaryView,
    TMCFinanceSummaryView,
    TMCRechargeRequestView,
    TMCRechargeOrderView,
    TMCRechargeVerifyView,
    TMCRechargeCancelView,
    RazorpayOrderView,
    RazorpayVerifyView,
    ConsultationVideoJoinView,
    ConsultationVideoRequestView,
    ConsultationVideoRespondView,
)
urlpatterns = [
    path("book-consultation/preview/", DirectBookingPreviewView.as_view(), name="direct-booking-preview"),
    path('doctor/availability/', DoctorAvailabilityView.as_view(), name="doctor-availability"),  # ✅ GET & PATCH
    path('doctor/availability/create/', DoctorAvailabilityCreateView.as_view(), name="doctor-availability-create"),  # ✅ NEW POST
    path('doctor/schedule/', DoctorScheduleView.as_view(), name="doctor-schedule"),
    path('doctor/schedule/<int:pk>/', DoctorScheduleDetailView.as_view(), name="doctor-schedule-detail"),
    path('doctor/pending-requests/', DoctorPendingRequestsView.as_view(), name="doctor-pending-requests"),  # ✅ NEW
    path('doctor/queued-consultations/', DoctorQueuedConsultationsView.as_view(), name="doctor-queued-consultations"),  # ✅ NEW
    path('available-doctors/', AvailableDoctorsView.as_view(), name="available-doctors"),
    path('book-consultation/', ConsultationBookingView.as_view(), name="book-consultation"),
    path('history/', ConsultationHistoryView.as_view(), name="consultation-history"),
    path('update-status/<int:pk>/', UpdateConsultationStatusView.as_view(), name="update-consultation-status"),
    path('doctor-response/<int:pk>/', DoctorResponseView.as_view(), name="doctor-response"),
    path('patient-response/<int:pk>/', PatientResponseView.as_view(), name="patient-response"),
    path("chat-history/<int:consultation_id>/", ConsultationChatHistoryView.as_view(), name="chat-history"),
    path("send-message/<int:consultation_id>/", SendMessageView.as_view(), name="send-message"),  # ✅ NEW
    path("start-consultation/<int:consultation_id>/", StartConsultationView.as_view(), name="start-consultation"),  # ✅ NEW
    path("complete-consultation/<int:consultation_id>/", CompleteConsultationView.as_view(), name="complete-consultation"),  # ✅ NEW
    path("active-consultation/", ActiveConsultationView.as_view(), name="active-consultation"),  # ✅ NEW
    path("followups/request/<int:consultation_id>/", PatientFollowUpRequestView.as_view(), name="patient-followup-request"),
    path("followups/<int:followup_id>/doctor-response/", DoctorFollowUpResponseView.as_view(), name="doctor-followup-response"),
    path("events/<int:consultation_id>/", ConsultationEventsView.as_view(), name="consultation-events"),
    path("video/join/<int:consultation_id>/", ConsultationVideoJoinView.as_view(), name="consultation-video-join"),
    path("video/request/<int:consultation_id>/", ConsultationVideoRequestView.as_view(), name="consultation-video-request"),
    path("video/respond/<int:consultation_id>/", ConsultationVideoRespondView.as_view(), name="consultation-video-respond"),
    path("tmc/summary/", TMCDashboardSummaryView.as_view(), name="tmc-summary"),
    path("tmc/finance-summary/", TMCFinanceSummaryView.as_view(), name="tmc-finance-summary"),
    path("tmc/recharge-requests/", TMCRechargeRequestView.as_view(), name="tmc-recharge-requests"),
    path("tmc/recharge-requests/<int:recharge_id>/razorpay/order/", TMCRechargeOrderView.as_view(), name="tmc-razorpay-order"),
    path("tmc/recharge-requests/<int:recharge_id>/razorpay/verify/", TMCRechargeVerifyView.as_view(), name="tmc-razorpay-verify"),
    path("tmc/recharge-requests/<int:recharge_id>/cancel/", TMCRechargeCancelView.as_view(), name="tmc-recharge-cancel"),
    path("tmc/consultations/", TMCConsultationListView.as_view(), name="tmc-consultations"),
    path("tmc/book-consultation/", TMCBookConsultationView.as_view(), name="tmc-book-consultation"),
    path("patient/wallet/", PatientWalletSummaryView.as_view(), name="patient-wallet-summary"),
    path("patient/wallet/recharge-requests/<int:recharge_id>/razorpay/order/", PatientWalletRechargeOrderView.as_view(), name="patient-wallet-razorpay-order"),
    path("patient/wallet/recharge-requests/<int:recharge_id>/razorpay/verify/", PatientWalletRechargeVerifyView.as_view(), name="patient-wallet-razorpay-verify"),
    path("patient/wallet/recharge-requests/<int:recharge_id>/cancel/", PatientWalletRechargeCancelView.as_view(), name="patient-wallet-recharge-cancel"),
    path("doctor/earnings-summary/", DoctorEarningsSummaryView.as_view(), name="doctor-earnings-summary"),
    path("payments/<int:payment_id>/razorpay/order/", RazorpayOrderView.as_view(), name="razorpay-order"),
    path("payments/<int:payment_id>/razorpay/verify/", RazorpayVerifyView.as_view(), name="razorpay-verify"),
    path("prescription/<int:consultation_id>/", PrescriptionView.as_view(), name="prescription"),
    path(
        "prescription/<int:consultation_id>/versions/",
        PrescriptionVersionsView.as_view(),
        name="prescription-versions",
    ),
    path("prescription/pdf/<int:prescription_id>/", PrescriptionPDFView.as_view(), name="prescription-pdf"),
    path("staff/wallet-topup/", StaffPatientWalletTopupView.as_view(), name="staff-patient-wallet-topup"),
    path("staff/patients/", StaffPatientListView.as_view(), name="staff-patient-list"),
    path("staff/patient-recharge-requests/", StaffPatientRechargeRequestListView.as_view(), name="staff-patient-recharge-list"),
    path(
        "staff/patient-recharge-requests/<int:recharge_id>/process/",
        StaffPatientRechargeRequestProcessView.as_view(),
        name="staff-patient-recharge-process",
    ),
    path("staff/tmc-wallet-topup/", StaffTMCWalletTopupView.as_view(), name="staff-tmc-wallet-topup"),
    path("staff/admin-platform-wallet-topup/", StaffAdminPlatformWalletTopupView.as_view(), name="staff-admin-platform-wallet-topup"),
    path("staff/tmcs/", StaffTMCListView.as_view(), name="staff-tmc-list"),
    path("staff/tmc-recharge-requests/", StaffTMCRechargeRequestListView.as_view(), name="staff-tmc-recharge-list"),
    path(
        "staff/tmc-recharge-requests/<int:recharge_id>/process/",
        StaffTMCRechargeRequestProcessView.as_view(),
        name="staff-tmc-recharge-process",
    ),
    path("staff/fee-settings/", StaffFeeSettingsView.as_view(), name="staff-fee-settings"),
    path("staff/doctors/", StaffDoctorVerificationListView.as_view(), name="staff-doctor-list"),
    path(
        "staff/doctors/<int:doctor_profile_id>/verification/",
        StaffDoctorVerificationUpdateView.as_view(),
        name="staff-doctor-verification",
    ),
    path("staff/reports/summary/", StaffOperationsReportView.as_view(), name="staff-operations-report"),
    path("staff/exports/consultations.csv", StaffExportConsultationsCSVView.as_view(), name="staff-export-consultations"),
    path("staff/exports/doctor-earnings.csv", StaffExportDoctorEarningsCSVView.as_view(), name="staff-export-doctor-earnings"),
    path("staff/exports/tmc-entries.csv", StaffExportTMCEntriesCSVView.as_view(), name="staff-export-tmc-entries"),
    path("staff/exports/patient-wallet.csv", StaffExportPatientWalletCSVView.as_view(), name="staff-export-patient-wallet"),
    path("staff/exports/summary.csv", StaffExportSummaryCSVView.as_view(), name="staff-export-summary"),
    path(
        "staff/audit/consultation/<int:consultation_id>/",
        StaffConsultationAuditView.as_view(),
        name="staff-consultation-audit",
    ),
    path("doctor/profile/", DoctorProfileCompletionView.as_view(), name="doctor-profile-completion"),
]
