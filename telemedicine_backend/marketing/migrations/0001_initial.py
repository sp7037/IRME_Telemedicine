from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CallbackRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("interest", models.CharField(choices=[("TMC", "Open Telemedicine Center"), ("COURSE", "Telemedicine Assistant Course"), ("CONSULTATION", "Patient Consultation"), ("GENERAL", "General Inquiry")], db_index=True, max_length=24)),
                ("name", models.CharField(max_length=120)),
                ("phone", models.CharField(db_index=True, max_length=24)),
                ("email", models.EmailField(blank=True, default="", max_length=254)),
                ("state", models.CharField(blank=True, db_index=True, default="", max_length=80)),
                ("city", models.CharField(blank=True, db_index=True, default="", max_length=80)),
                ("message", models.TextField(blank=True, default="")),
                ("source_path", models.CharField(blank=True, default="", max_length=220)),
                ("status", models.CharField(choices=[("NEW", "New"), ("CONTACTED", "Contacted"), ("CLOSED", "Closed")], db_index=True, default="NEW", max_length=20)),
                ("admin_note", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="MarketingLandingPage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("page_type", models.CharField(choices=[("TMC", "Telemedicine Center"), ("COURSE", "Telemedicine Assistant Course")], db_index=True, max_length=20)),
                ("state", models.CharField(db_index=True, max_length=80)),
                ("city", models.CharField(blank=True, db_index=True, default="", max_length=80)),
                ("slug", models.SlugField(max_length=160, unique=True)),
                ("title", models.CharField(max_length=180)),
                ("meta_description", models.CharField(max_length=300)),
                ("h1", models.CharField(max_length=180)),
                ("intro", models.TextField(blank=True, default="")),
                ("body", models.TextField(blank=True, default="")),
                ("priority", models.PositiveSmallIntegerField(db_index=True, default=50)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["page_type", "state", "city", "priority"],
                "indexes": [models.Index(fields=["page_type", "is_active", "state", "city"], name="marketing_m_page_t_8dc654_idx")],
            },
        ),
    ]
