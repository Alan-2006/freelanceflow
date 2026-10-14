import os
import sys
from pathlib import Path

# Add project root to sys.path for serverless execution
CURRENT_DIR = Path(__file__).resolve().parent
BASE_DIR = CURRENT_DIR.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Use production settings for Vercel
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')

from django.core.wsgi import get_wsgi_application

# Vercel looks for 'app' as the WSGI callable
app = get_wsgi_application()

# Run migrations once if using /tmp/db.sqlite3 fallback
try:
    from django.conf import settings
    db_engine = settings.DATABASES.get('default', {}).get('ENGINE', '')
    if 'sqlite3' in db_engine and not os.path.exists('/tmp/.migrated'):
        from django.core.management import call_command
        call_command('migrate', interactive=False)
        with open('/tmp/.migrated', 'w') as f:
            f.write('1')
except Exception as e:
    print(f"Auto-migration note: {e}")

