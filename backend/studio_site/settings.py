"""Settings come from environment variables set in compose.yaml; the defaults match that file."""

import os
from pathlib import Path

SECRET_KEY = os.environ.get("STUDIO_SECRET_KEY", "local-development-only")
DEBUG = os.environ.get("STUDIO_DEBUG", "0") == "1"
ALLOWED_HOSTS = os.environ.get("STUDIO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
"""Only names that mean this PC: another site pointing its own name at 127.0.0.1 (DNS rebinding) is refused."""

INSTALLED_APPS = ["corsheaders", "studio"]
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "studio.origin_guard.OriginGuardMiddleware",
    "django.middleware.common.CommonMiddleware",
]
ROOT_URLCONF = "studio_site.urls"
WSGI_APPLICATION = "studio_site.wsgi.application"
CORS_ALLOWED_ORIGINS = os.environ.get("STUDIO_CORS_ORIGINS", "http://localhost:3000").split(",")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": os.environ.get("META_DB_HOST", "meta-db"),
        "PORT": os.environ.get("META_DB_PORT", "5432"),
        "NAME": os.environ.get("META_DB_NAME", "studio"),
        "USER": os.environ.get("META_DB_USER", "studio"),
        "PASSWORD": os.environ.get("META_DB_PASSWORD", "studio"),
    }
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = "UTC"

VECTOR_ADMIN_URL = os.environ.get("VECTOR_ADMIN_URL", "postgresql://vectors:vectors@pgvector:5432/postgres")
QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")
CONTROL_URL = os.environ.get("CONTROL_URL", "http://control:9000")
MODELS_DIR = Path(os.environ.get("MODELS_DIR", "/models"))
MODELS_HOST_DIR = os.environ.get(
    "MODELS_HOST_DIR",
    r"\\wsl.localhost\docker-desktop\mnt\docker-desktop-disk\data\docker\volumes\rag-studio_models\_data",
)
GPU_AVAILABLE = os.environ.get("GPU_AVAILABLE", "0") == "1"
HOST_DRIVES_ROOT = Path(os.environ.get("HOST_DRIVES_ROOT", "/host"))
GLOSSARY_VAULT_DIR = Path(os.environ.get("GLOSSARY_VAULT_DIR", "/vault"))
