"""Disposable GitHub Actions PostgreSQL only; never use to serve an application."""
import os
import socket
from django.core.exceptions import ImproperlyConfigured
from .settings import *

if os.getenv("GITHUB_ACTIONS") != "true":
    raise ImproperlyConfigured("ci_settings is restricted to the disposable GitHub Actions test job.")
DEBUG = False
SECRET_KEY = "ci-only-not-a-runtime-secret-000000000000000000000000000"
DATABASES = {"default": {"ENGINE": "django.db.backends.postgresql", "NAME": "postgres",
    "USER": "postgres", "PASSWORD": "ci-only-password", "HOST": "127.0.0.1", "PORT": "5432",
    "TEST": {"NAME": "test_telemedicine_ci"}}}
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
MEDIA_ROOT = BASE_DIR / "test-media"
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
RAZORPAY_ENABLED = False
RAZORPAY_KEY_ID = RAZORPAY_KEY_SECRET = ""
CLOUDFLARE_ACCOUNT_ID = CLOUDFLARE_API_TOKEN = CLOUDFLARE_CALLS_APP_ID = ""
CLOUDFLARE_REALTIMEKIT_ENABLED = False
DYTE_ENABLED = False
DYTE_API_KEY = DYTE_ORGANIZATION_ID = ""
_original_connect = socket.socket.connect


def _test_connect(sock, address):
    if isinstance(address, tuple) and address[0] not in ("127.0.0.1", "localhost", "::1"):
        raise OSError("External service access is disabled in the isolated test job.")
    return _original_connect(sock, address)


socket.socket.connect = _test_connect
