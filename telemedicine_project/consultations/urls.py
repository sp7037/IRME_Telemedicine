from django.urls import path
from .views import DoctorAvailabilityView, DoctorAvailabilityCreateView, DoctorResponseView, DoctorScheduleView, AvailableDoctorsView,ConsultationBookingView, PatientResponseView
from .views import ConsultationHistoryView, DoctorPendingRequestsView
from .views import UpdateConsultationStatusView
from consultations.views import ConsultationChatHistoryView, SendMessageView
from consultations.views import PrescriptionView
from consultations.views import PrescriptionPDFView
from consultations.views import DoctorProfileCompletionView
from consultations.views import DoctorQueuedConsultationsView, StartConsultationView, CompleteConsultationView, ActiveConsultationView
from consultations.views import (
    ConsultationEventsView,
    TMCDashboardSummaryView,
    TMCConsultationListView,
    TMCBookConsultationView,
    PatientWalletSummaryView,
    DoctorEarningsSummaryView,
    TMCFinanceSummaryView,
)
urlpatterns = [
    path('doctor/availability/', DoctorAvailabilityView.as_view(), name="doctor-availability"),  # ✅ GET & PATCH
    path('doctor/availability/create/', DoctorAvailabilityCreateView.as_view(), name="doctor-availability-create"),  # ✅ NEW POST
    path('doctor/schedule/', DoctorScheduleView.as_view(), name="doctor-schedule"),
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
    path("events/<int:consultation_id>/", ConsultationEventsView.as_view(), name="consultation-events"),
    path("tmc/summary/", TMCDashboardSummaryView.as_view(), name="tmc-summary"),
    path("tmc/finance-summary/", TMCFinanceSummaryView.as_view(), name="tmc-finance-summary"),
    path("tmc/consultations/", TMCConsultationListView.as_view(), name="tmc-consultations"),
    path("tmc/book-consultation/", TMCBookConsultationView.as_view(), name="tmc-book-consultation"),
    path("patient/wallet/", PatientWalletSummaryView.as_view(), name="patient-wallet-summary"),
    path("doctor/earnings-summary/", DoctorEarningsSummaryView.as_view(), name="doctor-earnings-summary"),
    path("prescription/<int:consultation_id>/", PrescriptionView.as_view(), name="prescription"),
    path("prescription/pdf/<int:prescription_id>/", PrescriptionPDFView.as_view(), name="prescription-pdf"),
    path("doctor/profile/", DoctorProfileCompletionView.as_view(), name="doctor-profile-completion"),
]
