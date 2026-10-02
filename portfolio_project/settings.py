import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

# ── Base directory ───────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# ── Load .env file (local development only; Vercel uses its own env vars) ────
load_dotenv(BASE_DIR / ".env")


# ── Small helpers for reading environment variables safely ───────────────────
def env_bool(name, default=False):
    """
    Reads True/False from the environment.

    os.environ always gives us TEXT, and in Python the text "False" counts as
    True. So we compare against an explicit list of "yes" words instead.
    """
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def env_int(name, default):
    """Reads a whole number from the environment, or returns the default."""
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw.strip())
    except ValueError:
        raise ImproperlyConfigured(f"{name} must be a whole number, but it is {raw!r}.")


def env_list(name):
    """Reads a comma-separated list (e.g. 'a.com, b.com') into a Python list."""
    raw = os.environ.get(name, "")
    return [item.strip() for item in raw.split(",") if item.strip()]


# ── Security ─────────────────────────────────────────────────────────────────
# Safe by default: if DEBUG isn't set, debug mode is OFF.
DEBUG = env_bool("DEBUG", default=False)

SECRET_KEY = os.environ.get("SECRET_KEY", "").strip()
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "insecure-development-only-key"
    else:
        raise ImproperlyConfigured(
            "SECRET_KEY is not set. Add it to your .env file (local) or to "
            "Vercel → Settings → Environment Variables (production)."
        )

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS") + [".vercel.app"]
if DEBUG:
    ALLOWED_HOSTS += ["localhost", "127.0.0.1"]

# Vercel serves the site over HTTPS and forwards requests to Django as plain
# HTTP, adding an "X-Forwarded-Proto: https" header. Telling Django to trust
# that header (and the vercel.app origins) is what lets the /admin/ login form
# pass Django's CSRF check in production.
CSRF_TRUSTED_ORIGINS = ["https://*.vercel.app"] + env_list("CSRF_TRUSTED_ORIGINS")

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# ── Installed apps ───────────────────────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",  # serves static files in dev too
    "django.contrib.staticfiles",
    "dashboard",  # our main app
]

# ── Middleware ───────────────────────────────────────────────────────────────
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # must be right after Security
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "portfolio_project.urls"

# ── Templates ────────────────────────────────────────────────────────────────
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "portfolio_project.wsgi.application"

# ── Database (PostgreSQL via Neon) ───────────────────────────────────────────
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    # Local SQLite file for development before Neon is configured.
    # (Vercel's file system is read-only, so production needs DATABASE_URL.)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ── Password validation ──────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── Internationalisation ─────────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Dhaka"
USE_I18N = True
USE_TZ = True

# ── Static files ─────────────────────────────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Django 5.1+ ignores the old STATICFILES_STORAGE setting; STORAGES is the
# current way. WhiteNoise's "CompressedManifest" storage gives every static
# file a fingerprinted, compressed copy so browsers cache them safely.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# ── Default primary key field ────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── GROQ API ─────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()

# ── GitHub API (optional token → 5,000 requests/hour instead of 60) ──────────
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()

# ── Server-side API cache lifetimes (seconds) — safe defaults if unset ───────
GITHUB_CACHE_TTL_SECONDS = env_int("GITHUB_CACHE_TTL_SECONDS", 3600)
CODEFORCES_CACHE_TTL_SECONDS = env_int("CODEFORCES_CACHE_TTL_SECONDS", 3600)