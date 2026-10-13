import os

from .base import *

DEBUG = env.bool('DEBUG', default=False)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*', '.vercel.app', 'localhost', '127.0.0.1'])

# Database configuration with Serverless / Vercel fallback
database_url = os.environ.get('DATABASE_URL', '').strip()
if database_url:
    DATABASES = {
        'default': env.db('DATABASE_URL')
    }
else:
    # Fallback to writable /tmp for serverless builds
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': '/tmp/db.sqlite3' if os.path.exists('/tmp') else BASE_DIR / 'db.sqlite3',
        }
    }

# Static files with WhiteNoise
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# Production security
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=False)
CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=False)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Trusted origins for Vercel
CSRF_TRUSTED_ORIGINS = env.list(
    'CSRF_TRUSTED_ORIGINS',
    default=[
        'https://*.vercel.app',
        'http://localhost:8000',
        'http://127.0.0.1:8000',
    ]
)
