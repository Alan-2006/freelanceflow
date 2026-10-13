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
