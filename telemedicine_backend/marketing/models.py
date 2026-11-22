from django.db import models
from django.utils import timezone


class MarketingLandingPage(models.Model):
    class PageType(models.TextChoices):
        TMC = "TMC", "Telemedicine Center"
        COURSE = "COURSE", "Telemedicine Assistant Course"

    page_type = models.CharField(max_length=20, choices=PageType.choices, db_index=True)
    state = models.CharField(max_length=80, db_index=True)
    city = models.CharField(max_length=80, blank=True, default="", db_index=True)
    slug = models.SlugField(max_length=160, unique=True)
    title = models.CharField(max_length=180)
    meta_description = models.CharField(max_length=300)
    h1 = models.CharField(max_length=180)
    intro = models.TextField(blank=True, default="")
    body = models.TextField(blank=True, default="")
    priority = models.PositiveSmallIntegerField(default=50, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["page_type", "state", "city", "priority"]
        indexes = [
            models.Index(
                fields=["page_type", "is_active", "state", "city"],
                name="marketing_m_page_t_8dc654_idx",
            ),
        ]

    def __str__(self):
        location = self.city or self.state
        return f"{self.get_page_type_display()} - {location}"


class CallbackRequest(models.Model):
    class Interest(models.TextChoices):
        TMC = "TMC", "Open Telemedicine Center"
        COURSE = "COURSE", "Telemedicine Assistant Course"
        CONSULTATION = "CONSULTATION", "Patient Consultation"
        GENERAL = "GENERAL", "General Inquiry"

    class Status(models.TextChoices):
        NEW = "NEW", "New"
        CONTACTED = "CONTACTED", "Contacted"
        CLOSED = "CLOSED", "Closed"

    interest = models.CharField(max_length=24, choices=Interest.choices, db_index=True)
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=24, db_index=True)
    email = models.EmailField(blank=True, default="")
    state = models.CharField(max_length=80, blank=True, default="", db_index=True)
    city = models.CharField(max_length=80, blank=True, default="", db_index=True)
    message = models.TextField(blank=True, default="")
    source_path = models.CharField(max_length=220, blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW, db_index=True)
    admin_note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_interest_display()} - {self.name} ({self.phone})"

