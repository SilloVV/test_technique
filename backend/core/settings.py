import os
from pathlib import Path

from dotenv import load_dotenv

# BASE_DIR pointe sur le dossier backend/
BASE_DIR = Path(__file__).resolve().parent.parent

# Charge les variables depuis backend/.env dans os.environ
# Si le fichier n'existe pas (CI/CD, prod), os.environ est déjà peuplé — pas d'erreur
load_dotenv(BASE_DIR / ".env")

# ─────────────────────────────────────────────────────────
# Sécurité
# ─────────────────────────────────────────────────────────

# clé
SECRET_KEY = os.environ["SECRET_KEY"]

# changer si prod ou dev
DEBUG = os.environ.get("DEBUG", "False") == "True"

# Hotes autorisés
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")


# ─────────────────────────────────────────────────────────
# Applications installées
# ─────────────────────────────────────────────────────────

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Support géospatial (PostGIS)
    "django.contrib.gis",
    # API REST
    "rest_framework",
    "rest_framework_gis",
    # CORS pour Angular
    "corsheaders",
    # Filtres de recherche
    "django_filters",
]

# ─────────────────────────────────────────────────────────
# Middleware
# ─────────────────────────────────────────────────────────

MIDDLEWARE = [
    # CorsMiddleware DOIT être en premier pour intercepter les requêtes OPTIONS
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "core.wsgi.application"


# ─────────────────────────────────────────────────────────
# Base de données
# ─────────────────────────────────────────────────────────

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# ─────────────────────────────────────────────────────────
# CORS — Autorisations cross-origin pour Angular
# ─────────────────────────────────────────────────────────

# Ex : CORS_ALLOWED_ORIGINS=http://localhost:4200,https://mon-app.fr
CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")


# ─────────────────────────────────────────────────────────
# Django REST Framework
# ─────────────────────────────────────────────────────────

REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
}


# ─────────────────────────────────────────────────────────
# Validation des mots de passe
# ─────────────────────────────────────────────────────────

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ─────────────────────────────────────────────────────────
# Internationalisation
# ─────────────────────────────────────────────────────────

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True


# ─────────────────────────────────────────────────────────
# Fichiers statiques & divers
# ─────────────────────────────────────────────────────────

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
