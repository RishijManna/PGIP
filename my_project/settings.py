from pathlib import Path
import os
import sys
import dj_database_url
from dotenv import load_dotenv

# =====================================
# Paths
# =====================================
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")
IS_TESTING = "test" in sys.argv

# =====================================
# Security
# =====================================
# DEBUG is opt-in. Production must never inherit a debug/default secret setup.
DEBUG = os.environ.get(
    "DEBUG",
    "False"
).lower() == "true"

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

if not SECRET_KEY:
    if DEBUG or IS_TESTING:
        SECRET_KEY = "local-development-only-secret-key"
    else:
        raise RuntimeError("DJANGO_SECRET_KEY must be set when DEBUG is False.")

# =====================================
# Host settings (IMPORTANT)
# =====================================
ALLOWED_HOSTS = [
    "rishijmanna.pythonanywhere.com",
    "localhost",
    "127.0.0.1",
]

CSRF_TRUSTED_ORIGINS = [
    "https://rishijmanna.pythonanywhere.com",
]

# =====================================
# Apps
# =====================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'my_app',
]

# =====================================
# Middleware
# =====================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',

    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'my_project.urls'

WSGI_APPLICATION = 'my_project.wsgi.application'

ASGI_APPLICATION = 'my_project.asgi.application'

# =====================================
# Templates
# =====================================
TEMPLATES = [
    {
        'BACKEND':
        'django.template.backends.django.DjangoTemplates',

        'DIRS': [
            BASE_DIR / 'core' / 'templates'
        ],

        'APP_DIRS': True,

        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',

                'django.contrib.auth.context_processors.auth',

                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# =====================================
# Database
# =====================================
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600
    )
}

if DATABASES['default']['ENGINE'] == \
        'django.db.backends.postgresql':

    DATABASES['default']['OPTIONS'] = {
        'sslmode': 'require'
    }

# =====================================
# Password validation
# =====================================
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME':
        'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.MinimumLengthValidator'
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.CommonPasswordValidator'
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.NumericPasswordValidator'
    },
]

# =====================================
# Internationalization
# =====================================
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# =====================================
# Static Files
# =====================================
STATIC_URL = '/static/'

STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = [
    BASE_DIR / 'core' / 'static'
]

STATICFILES_STORAGE = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
)

# =====================================
# Media Files
# =====================================
MEDIA_URL = '/media/'

MEDIA_ROOT = BASE_DIR / 'media'

# =====================================
# Authentication
# =====================================
LOGIN_URL = '/login/'

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

if not DEBUG and not IS_TESTING:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "True").lower() == "true"
    SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True


# =====================================
# Email
# =====================================
EMAIL_BACKEND = (
    'django.core.mail.backends.smtp.EmailBackend'
)

EMAIL_HOST = 'smtp.gmail.com'

EMAIL_PORT = 587

EMAIL_USE_TLS = True

EMAIL_HOST_USER = os.environ.get(
    "EMAIL_HOST_USER"
)

EMAIL_HOST_PASSWORD = os.environ.get(
    "EMAIL_HOST_PASSWORD"
)

# =====================================
# OpenAI
# =====================================
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_TIMEOUT = int(os.environ.get("OPENAI_TIMEOUT", "20"))
OPENAI_TEMPERATURE = float(os.environ.get("OPENAI_TEMPERATURE", "0.25"))
OPENAI_TOP_P = float(os.environ.get("OPENAI_TOP_P", "0.9"))

# =====================================
# Default Auto Field
# =====================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
