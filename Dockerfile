# AIC Cloud: repository root, Dockerfile builder, container port 8000.
FROM node:22-bookworm-slim AS frontend
WORKDIR /frontend
COPY telemedicine-frontend/package.json telemedicine-frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY telemedicine-frontend/ ./
ARG REACT_APP_API_BASE_URL=/api
ARG REACT_APP_MEDIA_BASE_URL=https://telemedicine.irme.in
ENV REACT_APP_API_BASE_URL=$REACT_APP_API_BASE_URL REACT_APP_MEDIA_BASE_URL=$REACT_APP_MEDIA_BASE_URL CI=false
RUN npm run build

FROM python:3.12-slim-bookworm AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=telemedicine_project.production_settings FRONTEND_DIST=/app/frontend PORT=8000
WORKDIR /app/backend
COPY telemedicine_backend/requirements.txt telemedicine_backend/requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock
COPY telemedicine_backend/ ./
COPY --from=frontend /frontend/build /app/frontend
COPY deploy/container-entrypoint.sh /app/container-entrypoint.sh
# Non-secret build-only values; they are not runtime defaults or database credentials.
RUN SECRET_KEY=build-only-placeholder-not-a-runtime-secret-00000000000000000000 \
    DB_NAME=build DB_USER=build DB_PASSWORD=build DB_HOST=localhost \
    UPLOAD_STORAGE=filesystem ALLOW_PERSISTENT_FILESYSTEM=true MEDIA_ROOT=/data/media \
    python manage.py collectstatic --noinput \
    && addgroup --system app && adduser --system --ingroup app --uid 10001 app \
    && mkdir -p /data/media && chown -R app:app /data /app \
    && chmod +x /app/container-entrypoint.sh
USER app
EXPOSE 8000
ENTRYPOINT ["/app/container-entrypoint.sh"]
