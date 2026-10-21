from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*', 'localhost', '127.0.0.1', 'testserver']

# Database defaults to SQLite in dev if DATABASE_URL is not provided or empty
database_url = env('DATABASE_URL', default='')
if not database_url:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': env.db('DATABASE_URL')
    }


# In dev, send emails to console by default
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Cache in-memory for dev
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'freelanceflow-dev-cache',
    }
}
