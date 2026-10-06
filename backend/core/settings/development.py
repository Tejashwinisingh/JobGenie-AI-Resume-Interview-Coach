"""
core/settings/development.py
Development-specific overrides — uses SQLite.
"""
from .base import *  # noqa: F401, F403

DEBUG = True

# Inherit DATABASES from base.py (auto-detects DATABASE_URL for Postgres, falls back to SQLite)

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver', '*']

# ─── CORS (allow React dev server) ────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
]
CORS_ALLOW_CREDENTIALS = True

# ─── DRF Browsable API in dev ─────────────────────────────────────────────────
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (  # noqa: F405
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',
)
