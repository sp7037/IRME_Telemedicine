"""Explicit server configuration. Local .env files are never loaded by this module."""
import os
from pathlib import Path
from urllib.parse import urlsplit, unquote, parse_qs
from django.core.exceptions import ImproperlyConfigured
from .settings import *


def required(name):
    value = os.environ.get(name, "").strip()
    if not value or value.startswith("your_") or value.startswith("replace-"):
        raise ImproperlyConfigured(f"Set {name} in the hosting environment.")
    return value


DEBUG = False
SECRET_KEY = required("SECRET_KEY")
if len(SECRET_KEY) < 50 or SECRET_KEY.startswith("django-insecure"):
    raise ImproperlyConfigured("Use a new random SECRET_KEY of at least 50 characters.")
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", ["telemedicine.irme.in"])
if "*" in ALLOWED_HOSTS:
    raise ImproperlyConfigured("Wildcard ALLOWED_HOSTS is not permitted.")
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "https://telemedicine.irme.in").rstrip("/")
if not FRONTEND_BASE_URL.startswith("https://"):
    raise ImproperlyConfigured("FRONTEND_BASE_URL must use HTTPS.")
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", [FRONTEND_BASE_URL])
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", [FRONTEND_BASE_URL])
database_url = os.getenv("DATABASE_URL", "").strip()
sslmode = os.getenv("DB_SSLMODE", "require")
if database_url:
    try:
        parts = urlsplit(database_url)
        if parts.scheme not in {"postgres", "postgresql"} or not all((parts.hostname, parts.username, parts.password, parts.path.strip("/"))):
            raise ValueError()
        db_values = dict(NAME=unquote(parts.path.lstrip("/")), USER=unquote(parts.username),
            PASSWORD=unquote(parts.password), HOST=parts.hostname, PORT=str(parts.port or 5432))
        sslmode = parse_qs(parts.query).get("sslmode", [sslmode])[0]
    except ValueError:
        raise ImproperlyConfigured("DATABASE_URL must be a valid PostgreSQL connection string.") from None
else:
    db_values = dict(NAME=required("DB_NAME"), USER=required("DB_USER"), PASSWORD=required("DB_PASSWORD"),
        HOST=required("DB_HOST"), PORT=os.getenv("DB_PORT", "5432"))
if sslmode not in {"require", "verify-ca", "verify-full", "disable"}:
    raise ImproperlyConfigured("Unsupported database SSL mode.")
if sslmode == "disable" and db_values["HOST"] not in {"localhost", "127.0.0.1", "::1"}:
    raise ImproperlyConfigured("External PostgreSQL connections require SSL.")
DATABASES["default"].update(**db_values, CONN_MAX_AGE=0, CONN_HEALTH_CHECKS=True)
DATABASES["default"]["OPTIONS"]["sslmode"] = sslmode
MEDIA_ROOT = Path(os.getenv("MEDIA_ROOT", "/tmp/irme-media"))  # Temporary buffers only with S3.
MEDIA_URL = "/media/"
FRONTEND_DIST = Path(os.getenv("FRONTEND_DIST", str(BASE_DIR.parent / "telemedicine-frontend/build")))
ROOT_URLCONF = "telemedicine_project.production_urls"
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static", FRONTEND_DIST / "static"]
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
WHITENOISE_ROOT = FRONTEND_DIST
WHITENOISE_MAX_AGE = 3600
STORAGES = {"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"}}
UPLOAD_STORAGE = os.getenv("UPLOAD_STORAGE", "s3")
if UPLOAD_STORAGE == "s3":
    endpoint = required("S3_ENDPOINT_URL")
    if not endpoint.startswith("https://"):
        raise ImproperlyConfigured("S3_ENDPOINT_URL must use HTTPS.")
    STORAGES["default"] = {
        "BACKEND": "telemedicine_project.upload_storage.PrivateS3Storage",
        "OPTIONS": {
            "bucket_name": required("S3_BUCKET_NAME"),
            "access_key": required("S3_ACCESS_KEY_ID"),
            "secret_key": required("S3_SECRET_ACCESS_KEY"),
            "endpoint_url": endpoint,
            "region_name": required("S3_REGION_NAME"),
            "addressing_style": os.getenv("S3_ADDRESSING_STYLE", "path"),
            "default_acl": None, "file_overwrite": False,
            "querystring_auth": True, "custom_domain": None,
        },
    }
elif UPLOAD_STORAGE != "filesystem" or os.getenv("ALLOW_PERSISTENT_FILESYSTEM") != "true":
    raise ImproperlyConfigured("Use private S3 uploads; filesystem requires an explicitly confirmed persistent volume.")
REST_FRAMEWORK = {**REST_FRAMEWORK, "DEFAULT_RENDERER_CLASSES": ["telemedicine_project.protected_media.MediaJSONRenderer"]}
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "3600"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024
DEPLOYMENT_STAGE = os.getenv("DEPLOYMENT_STAGE", "staging")
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "").strip()
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "").strip()
RAZORPAY_ENABLED = bool(RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)
if DEPLOYMENT_STAGE not in {"staging", "production"}:
    raise ImproperlyConfigured("DEPLOYMENT_STAGE must be staging or production.")
# The old API-only policy blocks React inline styles and external video/checkout.
# Observe staging integrations before enforcing their explicit production allowlists.
CSP_REPORT_ONLY = DEPLOYMENT_STAGE == "staging"
CSP_STYLE_SRC = tuple(env_list("CSP_STYLE_SRC", ["'self'", "'unsafe-inline'"]))
CSP_SCRIPT_SRC = tuple(env_list("CSP_SCRIPT_SRC", ["'self'", "https://checkout.razorpay.com", "https://cdn.razorpay.com"]))
CSP_IMG_SRC = tuple(env_list("CSP_IMG_SRC", ["'self'", "data:", "blob:"]))
CSP_MEDIA_SRC = ("'self'", "blob:")
CSP_WORKER_SRC = ("'self'", "blob:")
CSP_OBJECT_SRC = ("'none'",)
CSP_BASE_URI = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)
CSP_FRAME_SRC = tuple(env_list("CSP_FRAME_SRC", ["'self'", "https://api.razorpay.com", "https://checkout.razorpay.com"]))
CSP_CONNECT_SRC = tuple(env_list("CSP_CONNECT_SRC", ["'self'", "https://api.razorpay.com",
    "https://*.cloudflare.com", "wss://*.cloudflare.com", "https://*.dyte.io", "wss://*.dyte.io"]))
if DEPLOYMENT_STAGE == "staging" and RAZORPAY_ENABLED and not RAZORPAY_KEY_ID.startswith("rzp_test_"):
    raise ImproperlyConfigured("Staging accepts only Razorpay test keys; remove live keys.")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "IRME Telemedicine <no-reply@irme.in>")
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
if DEPLOYMENT_STAGE == "production":
    required("EMAIL_HOST")
    if "console" in EMAIL_BACKEND:
        raise ImproperlyConfigured("Production emails must not be printed into console logs.")
