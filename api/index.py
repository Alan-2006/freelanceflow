import os
import shutil
import sys
import traceback
from pathlib import Path

# Add project root to sys.path for serverless execution
CURRENT_DIR = Path(__file__).resolve().parent
BASE_DIR = CURRENT_DIR.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Use production settings for Vercel
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')

# Fast SQLite fallback: copy pre-migrated sqlite db to /tmp if using sqlite
try:
    tmp_dir = Path('/tmp')
    if tmp_dir.exists():
        tmp_db = tmp_dir / 'db.sqlite3'
        src_db = BASE_DIR / 'db.sqlite3'
        if not tmp_db.exists() and src_db.exists():
            shutil.copyfile(src_db, tmp_db)
except Exception as e:
    print(f"Warning copying SQLite db: {e}", file=sys.stderr)

from django.core.wsgi import get_wsgi_application

_application = get_wsgi_application()

def app(environ, start_response):
    """WSGI callable for Vercel with graceful error capture."""
    try:
        return _application(environ, start_response)
    except Exception:
        err_msg = traceback.format_exc()
        print(f"Serverless invocation error:\n{err_msg}", file=sys.stderr)
        status = '500 Internal Server Error'
        headers = [('Content-Type', 'text/html; charset=utf-8')]
        start_response(status, headers)
        body = (
            "<!DOCTYPE html><html><head><title>FreelanceFlow Error</title></head>"
            "<body style='font-family:sans-serif;padding:2rem;background:#0f172a;color:#f8fafc;'>"
            "<h1>FreelanceFlow - Runtime Error</h1>"
            f"<pre style='background:#1e293b;padding:1.5rem;border-radius:8px;overflow:auto;'>{err_msg}</pre>"
            "</body></html>"
        )
        return [body.encode('utf-8')]
