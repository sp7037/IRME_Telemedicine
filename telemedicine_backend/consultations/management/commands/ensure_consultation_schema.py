"""
Repair consultations_consultation columns when migration 0009 could not complete
(e.g. prescription medicines JSON conversion failed). Safe to run multiple times.

Usage:
    python manage.py ensure_consultation_schema

Then fix prescription data and run migrations, or continue using the app once columns exist.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import connection


def _pg_column_exists(cursor, table: str, column: str) -> bool:
    cursor.execute(
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s AND column_name = %s
        """,
        [table, column],
    )
    return cursor.fetchone() is not None


def _sqlite_column_exists(cursor, table: str, column: str) -> bool:
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


class Command(BaseCommand):
    help = "Add missing Consultation columns (updated_at, last_status_changed_at, etc.) without running full migrations."

    def handle(self, *args, **options):
        table = "consultations_consultation"
        user_table = get_user_model()._meta.db_table
        added = []

        with connection.cursor() as cursor:
            if connection.vendor == "postgresql":

                def col(name: str) -> bool:
                    return _pg_column_exists(cursor, table, name)

                if not col("updated_at"):
                    cursor.execute(
                        f'ALTER TABLE "{table}" ADD COLUMN "updated_at" timestamp with time zone NOT NULL DEFAULT NOW()'
                    )
                    added.append("updated_at")

                if not col("last_status_changed_at"):
                    cursor.execute(
                        f'ALTER TABLE "{table}" ADD COLUMN "last_status_changed_at" timestamp with time zone'
                    )
                    cursor.execute(
                        f'UPDATE "{table}" SET last_status_changed_at = created_at WHERE last_status_changed_at IS NULL'
                    )
                    cursor.execute(
                        f'ALTER TABLE "{table}" ALTER COLUMN "last_status_changed_at" SET NOT NULL'
                    )
                    cursor.execute(
                        f'ALTER TABLE "{table}" ALTER COLUMN "last_status_changed_at" SET DEFAULT NOW()'
                    )
                    added.append("last_status_changed_at")

                if not col("terminal_reason"):
                    cursor.execute(
                        f'ALTER TABLE "{table}" ADD COLUMN "terminal_reason" text NULL'
                    )
                    added.append("terminal_reason")

                if not col("status_changed_by_id"):
                    cursor.execute(
                        f'ALTER TABLE "{table}" ADD COLUMN "status_changed_by_id" bigint NULL '
                        f'REFERENCES "{user_table}" ("id") ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED'
                    )
                    added.append("status_changed_by_id")

                if not col("queue_number"):
                    cursor.execute(
                        f'ALTER TABLE "{table}" ADD COLUMN "queue_number" integer NULL'
                    )
                    added.append("queue_number")

            elif connection.vendor == "sqlite":

                def col(name: str) -> bool:
                    return _sqlite_column_exists(cursor, table, name)

                if not col("updated_at"):
                    cursor.execute(
                        f'ALTER TABLE "{table}" ADD COLUMN updated_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP'
                    )
                    added.append("updated_at")

                if not col("last_status_changed_at"):
                    cursor.execute(
                        f'ALTER TABLE "{table}" ADD COLUMN last_status_changed_at datetime NULL'
                    )
                    cursor.execute(
                        f'UPDATE "{table}" SET last_status_changed_at = created_at WHERE last_status_changed_at IS NULL'
                    )
                    added.append("last_status_changed_at")

                if not col("terminal_reason"):
                    cursor.execute(
                        f'ALTER TABLE "{table}" ADD COLUMN terminal_reason text NULL'
                    )
                    added.append("terminal_reason")

                if not col("status_changed_by_id"):
                    cursor.execute(
                        f'ALTER TABLE "{table}" ADD COLUMN status_changed_by_id bigint NULL REFERENCES "{user_table}" ("id")'
                    )
                    added.append("status_changed_by_id")

                if not col("queue_number"):
                    cursor.execute(
                        f'ALTER TABLE "{table}" ADD COLUMN queue_number integer NULL'
                    )
                    added.append("queue_number")

            else:
                self.stdout.write(self.style.WARNING(f"Vendor {connection.vendor} not supported; use PostgreSQL or SQLite."))
                return

        if added:
            self.stdout.write(self.style.SUCCESS(f"Added columns: {', '.join(added)}"))
        else:
            self.stdout.write("No missing columns detected on consultations_consultation.")

        self.stdout.write(
            "\nIf `python manage.py migrate` still fails on consultations.0009, fix invalid "
            "prescription `medicines` values (must be valid JSON array), then migrate. "
            "Example check (PostgreSQL):\n"
            "  SELECT id, medicines FROM consultations_prescription WHERE medicines::text NOT LIKE '[%';\n"
        )
