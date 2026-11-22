#!/bin/sh
set -eu
python manage.py check --deploy --fail-level ERROR
python manage.py deploy_release
exec gunicorn telemedicine_project.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" --workers "${WEB_CONCURRENCY:-1}" \
  --worker-class gthread --threads "${GUNICORN_THREADS:-4}" --timeout 90 \
  --access-logfile - --error-logfile - \
  --access-logformat '%(h)s %(m)s %(U)s %(s)s %(L)s'
