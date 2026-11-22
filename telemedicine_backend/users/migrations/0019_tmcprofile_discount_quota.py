from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0018_tmcprofilechangerequest_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="tmcprofile",
            name="discount_percentage",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text="Discount percentage applied after free consultations are exhausted.",
                max_digits=5,
            ),
        ),
        migrations.AddField(
            model_name="tmcprofile",
            name="discounted_consultation_quota",
            field=models.PositiveIntegerField(
                default=0,
                help_text="Number of discounted consultations allowed after free quota.",
            ),
        ),
        migrations.AddField(
            model_name="tmcprofile",
            name="discounted_consultations_used",
            field=models.PositiveIntegerField(
                default=0,
                help_text="Number of discounted consultations already used.",
            ),
        ),
    ]
