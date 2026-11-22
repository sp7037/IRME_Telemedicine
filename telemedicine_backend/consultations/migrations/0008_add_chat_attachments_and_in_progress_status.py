# Generated manually on 2025-12-06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('consultations', '0007_consultation_queue_number_alter_consultation_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='consultation',
            name='status',
            field=models.CharField(
                choices=[
                    ('PENDING', 'Waiting for Doctor'), 
                    ('ACCEPTED', 'Accepted by Doctor'), 
                    ('QUEUED', 'Doctor Put in Queue'), 
                    ('IN_PROGRESS', 'Consultation In Progress'),
                    ('POSTPONED', 'Doctor Suggested Another Time'), 
                    ('CANCELED', 'Canceled by Patient/TMC'), 
                    ('COMPLETED', 'Consultation Completed'), 
                    ('REJECTED', 'Rejected by Doctor'), 
                    ('REJECTED_BY_PATIENT', 'Postponed Time Rejected by Patient')
                ], 
                db_index=True, 
                default='PENDING', 
                max_length=20
            ),
        ),
        migrations.AlterField(
            model_name='consultationchat',
            name='message',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='consultationchat',
            name='attachment',
            field=models.FileField(
                blank=True, 
                help_text='Image or PDF file attachment', 
                null=True, 
                upload_to='chat_attachments/%Y/%m/%d/'
            ),
        ),
        migrations.AddField(
            model_name='consultationchat',
            name='attachment_type',
            field=models.CharField(
                blank=True, 
                help_text='Type of attachment: image, pdf, or other', 
                max_length=20, 
                null=True
            ),
        ),
    ]




