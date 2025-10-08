from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv

# =======================
# Paths
# =======================
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env (only works locally, Render ignores this)
load_dotenv()

# =======================
# Security
# =======================
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "unsafe-secret-key")
DEBUG = os.environ.get("DEBUG", "True") == "True"

# Render sets this automatically
RENDER_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
ALLOWED_HOSTS = (
    [RENDER_HOSTNAME] if RENDER_HOSTNAME else ['.onrender.com', 'localhost', '127.0.0.1']
)
DEBUG = False
ALLOWED_HOSTS = ['RishijManna.pythonanywhere.com']
# =======================
# Applications
# =======================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'my_app',  # replace with your app name(s)
]

# =======================
# Middleware
# =======================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ✅ Static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'my_project.urls'  # replace with your project name

# =======================
# Templates
# =======================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'core' / 'templates'],
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

WSGI_APPLICATION = 'my_project.wsgi.application'  # replace with your project name
ASGI_APPLICATION = 'my_project.asgi.application'  # if you’re using ASGI

# =======================
# Database
# =======================
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600
    )
}

# Force SSL only if Postgres (Render)
if DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql':
    DATABASES['default']['OPTIONS'] = {'sslmode': 'require'}

# =======================
# Password validation
# =======================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# =======================
# Internationalization
# =======================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# =======================
# Static files
# =======================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / 'core' / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# =======================
# Media files
# =======================
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# =======================
# Authentication
# =======================
LOGIN_URL = '/login/'

# =======================
# Email
# =======================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")

# =======================
# Default PK field
# =======================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
