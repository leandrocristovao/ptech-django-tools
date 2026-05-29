from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SECRET_KEY = "not-a-secret"
DEBUG = True
USE_TZ = True
TIME_ZONE = "UTC"
INSTALLED_APPS = [
    "ptech_tools.apps.PtechToolsConfig",
]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
PTECH_TOOLS = {}
