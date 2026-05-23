from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("consultations", "0018_patientwalletrechargerequest"),
        ("users", "0019_tmcprofile_discount_quota"),
    ]

    operations = [
        migrations.AddField(
            model_name="consultationfeesetting",
            name="platform_fee_percentage",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text="Platform/service fee percentage charged on the doctor's consultation fee.",
                max_digits=5,
            ),
        ),
        migrations.AlterField(
            model_name="consultationfinance",
            name="payer_entity",
            field=models.CharField(
                choices=[
                    ("PATIENT", "Patient"),
                    ("TMC", "TMC"),
                    ("ADMIN", "Admin / Platform"),
                    ("NONE", "None"),
                ],
                db_index=True,
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="consultationfinance",
            name="admin_subsidy_amount",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name="consultationfinance",
            name="discount_amount",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name="consultationfinance",
            name="doctor_fee",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name="consultationfinance",
            name="platform_fee",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.CreateModel(
            name="AdminPlatformAccount",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(default="Platform Wallet", max_length=80, unique=True)),
                ("balance", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("total_credited", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("total_debited", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("total_platform_fees", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("total_doctor_subsidies", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="AdminPlatformEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "entry_type",
                    models.CharField(
                        choices=[
                            ("CREDIT", "Credit"),
                            ("PLATFORM_FEE", "Platform Fee"),
                            ("DOCTOR_SUBSIDY", "Doctor Subsidy"),
                            ("ADJUSTMENT", "Adjustment"),
                        ],
                        db_index=True,
                        max_length=20,
                    ),
                ),
                ("amount", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("balance_after", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("description", models.CharField(blank=True, max_length=255, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="entries",
                        to="consultations.adminplatformaccount",
                    ),
                ),
                (
                    "consultation",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="admin_platform_entries",
                        to="consultations.consultation",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
