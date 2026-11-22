# Fixes DBs where Consultation.updated_at is missing (e.g. 0009 failed partway).

from django.db import migrations


def ensure_consultation_updated_at(apps, schema_editor):
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        if connection.vendor == "postgresql":
            cursor.execute(
                """
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'consultations_consultation'
                  AND column_name = 'updated_at'
                """
            )
            if cursor.fetchone():
                return
            cursor.execute(
                """
                ALTER TABLE consultations_consultation
                ADD COLUMN updated_at timestamp with time zone NOT NULL DEFAULT NOW()
                """
            )
        elif connection.vendor == "sqlite":
            cursor.execute("PRAGMA table_info(consultations_consultation)")
            cols = [row[1] for row in cursor.fetchall()]
            if "updated_at" in cols:
                return
            cursor.execute(
                """
                ALTER TABLE consultations_consultation
                ADD COLUMN updated_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP
                """
            )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("consultations", "0011_prescription_version_and_updated_at"),
    ]

    operations = [
        migrations.RunPython(ensure_consultation_updated_at, noop_reverse),
    ]
