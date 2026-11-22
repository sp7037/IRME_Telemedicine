from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("consultations", "0020_consultationvideosession"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tmcrechargerequest",
            name="status",
            field=models.CharField(
                choices=[
                    ("PENDING", "Pending"),
                    ("APPROVED", "Approved"),
                    ("REJECTED", "Rejected"),
                    ("CANCELED", "Canceled"),
                ],
                db_index=True,
                default="PENDING",
                max_length=12,
            ),
        ),
        migrations.AddField(
            model_name="tmcrechargerequest",
            name="provider",
            field=models.CharField(
                choices=[("MANUAL", "Manual / Admin Approval"), ("RAZORPAY", "Razorpay")],
                db_index=True,
                default="MANUAL",
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name="tmcrechargerequest",
            name="gateway_order_id",
            field=models.CharField(blank=True, db_index=True, max_length=120, null=True),
        ),
        migrations.AddField(
            model_name="tmcrechargerequest",
            name="gateway_payment_id",
            field=models.CharField(blank=True, max_length=120, null=True),
        ),
        migrations.AddField(
            model_name="tmcrechargerequest",
            name="gateway_signature",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="tmcrechargerequest",
            name="gateway_payload",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
