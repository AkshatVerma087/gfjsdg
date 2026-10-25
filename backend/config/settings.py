"""Django settings for Wind Forecast Monitor.

All configuration is driven by the typed Settings object in config/env.py.
"""

import urllib.parse
from pathlib import Path

from config.env import settings

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = settings.django_secret_key.get_secret_value()
DEBUG = settings.django_debug
ALLOWED_HOSTS = settings.allowed_hosts_list + (["testserver"] if not settings.is_production else [])

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "core.apps.CoreConfig",
    "wind.apps.WindConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "core.middleware.RequestIDMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR.parent / "frontend" / "dist"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database configuration
_db_url = urllib.parse.urlparse(settings.database_url)
if _db_url.scheme in ("postgresql", "postgres"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": _db_url.path.lstrip("/"),
            "USER": _db_url.username or "",
            "PASSWORD": _db_url.password or "",
            "HOST": _db_url.hostname or "localhost",
            "PORT": _db_url.port or 5432,
            "CONN_MAX_AGE": 600 if settings.is_production else 0,
        }
    }
elif _db_url.scheme == "sqlite":
    _sqlite_path = (
        _db_url.path[1:]
        if _db_url.path.startswith("//")
        else (_db_url.path.lstrip("/") or ":memory:")
    )
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": _sqlite_path,
        }
    }
else:
    raise ValueError(f"Unsupported database scheme: {_db_url.scheme}")

# Internationalization & Timezones
LANGUAGE_CODE = "en-gb"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_ROOT.mkdir(exist_ok=True)
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
WHITENOISE_ROOT = BASE_DIR.parent / "frontend" / "dist"

# Security Headers & Hardening
if settings.is_production:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
else:
    SECURE_SSL_REDIRECT = False

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
DATA_UPLOAD_MAX_MEMORY_SIZE = 262144  # 256 KB limit for read-only analytical workloads

# Logging configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "request_id": {
            "()": "core.logging.RequestIDFilter",
        },
        "redact_secrets": {
            "()": "core.logging.SecretRedactionFilter",
        },
    },
    "formatters": {
        "json": {
            "()": "core.logging.JSONFormatter",
        },
        "readable": {
            "format": "%(asctime)s [%(levelname)s] [%(name)s] [%(request_id)s] %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": ["request_id", "redact_secrets"],
            "formatter": "json" if settings.is_production else "readable",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO" if settings.is_production else "DEBUG",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "core.access": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
