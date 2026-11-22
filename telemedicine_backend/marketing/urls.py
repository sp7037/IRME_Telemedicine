from django.urls import path

from .views import CallbackRequestView, MarketingLandingPageDetailView, MarketingLandingPageListView

urlpatterns = [
    path("callback/", CallbackRequestView.as_view(), name="marketing-callback"),
    path("landing-pages/", MarketingLandingPageListView.as_view(), name="marketing-landing-pages"),
    path("landing-pages/<slug:slug>/", MarketingLandingPageDetailView.as_view(), name="marketing-landing-page-detail"),
]
