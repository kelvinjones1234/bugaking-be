import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# =========================================================
#  Load Environment Variables
# =========================================================
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)


# Utility function to get environment variables
def get_env_variable(var_name, default=None):
    value = os.getenv(var_name, default)
    if value is None:
        raise ImproperlyConfigured(f"Set the {var_name} environment variable")
    return value


# =========================================================
#  Core Settings
# =========================================================

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_env_variable("SECRET_KEY", "fallback-unsafe-secret-key-change-me")

# FIX: Correct Logic for DEBUG
# If DJANGO_ENV is 'production', DEBUG should be False.
ENVIRONMENT = get_env_variable("DJANGO_ENV", "production")
DEBUG = ENVIRONMENT == "production" 

ALLOWED_HOSTS = [
    "bugaking.pythonanywhere.com",
    "localhost",
    "127.0.0.1",
    "31d3954f598a.ngrok-free.app",
]


# =========================================================
#  Applications
# =========================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "cloudinary_storage",  
    "cloudinary",
    # Custom Apps
    "account",
    "investment",
    "portfolio",
    "documents",
    "notification",
    "payment",
    # Third Party Apps
    "rest_framework",
    "corsheaders",
    "django_filters",
    "rest_framework_simplejwt",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware", # Critical for serving static files
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

AUTH_USER_MODEL = "account.User"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"


# =========================================================
#  Database
# =========================================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# =========================================================
#  Authentication & API
# =========================================================
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    { "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator" },
    { "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator" },
    { "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator" },
    { "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator" },
]


# =========================================================
#  Email Configuration
# =========================================================
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = get_env_variable("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(get_env_variable("EMAIL_PORT", "465"))
EMAIL_USE_SSL = get_env_variable("EMAIL_USE_SSL", "True").lower() == "true"
EMAIL_USE_TLS = get_env_variable("EMAIL_USE_TLS", "False").lower() == "true"
EMAIL_HOST_USER = get_env_variable("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = get_env_variable("EMAIL_HOST_PASSWORD")


# =========================================================
#  Internationalization
# =========================================================
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# =========================================================
#  Static & Media Files (Crucial Fixes Here)
# =========================================================

# 1. Cloudinary Credentials
CLOUDINARY_STORAGE = {
    "CLOUD_NAME": get_env_variable("CLOUDINARY_CLOUD_NAME"),
    "API_KEY": get_env_variable("CLOUDINARY_API_KEY"),
    "API_SECRET": get_env_variable("CLOUDINARY_API_SECRET"),
}

# 2. Static Files (CSS/JS)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# FIX: Explicitly define Finders so Django knows where to look for Admin CSS
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

# FIX: Explicitly define the local static directory (Create this folder if it doesn't exist)
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# 3. Media Files (Images/Videos)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# 4. Storage Configuration (Django 4.2+)
# We use standard storage for static files (to avoid WhiteNoise crash)
# We use Cloudinary for media files.
STORAGES = {
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
}


STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# =========================================================
#  CORS Settings
# =========================================================
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "https://bugaking.vercel.app",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
    "https://31d3954f598a.ngrok-free.app",
]

CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^http:\/\/.*\.localhost:3000$",
    r"^http:\/\/.*\.127.0.0.1:3000$",
]

CSRF_TRUSTED_ORIGINS = [
    "https://31d3954f598a.ngrok-free.app",
    "https://bugaking.vercel.app",
]