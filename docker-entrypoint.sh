#!/usr/bin/env bash
set -e

echo "==> FreelanceFlow Docker Entrypoint Initializing..."

# Wait for PostgreSQL if DATABASE_URL is set
if [ -n "$DATABASE_URL" ]; then
    echo "Waiting for PostgreSQL database to accept connections..."
    python -c "
import sys, time, os, urllib.parse
import psycopg2

db_url = os.environ.get('DATABASE_URL', '')
if db_url:
    result = urllib.parse.urlparse(db_url)
    username = result.username
    password = result.password
    database = result.path[1:]
    hostname = result.hostname
    port = result.port or 5432
    for attempt in range(30):
        try:
            conn = psycopg2.connect(
                dbname=database,
                user=username,
                password=password,
                host=hostname,
                port=port,
                connect_timeout=3
            )
            conn.close()
            print('PostgreSQL is online and reachable!')
            sys.exit(0)
        except Exception as e:
            time.sleep(1)
    print('Failed to connect to PostgreSQL within 30 seconds.')
    sys.exit(1)
" || exit 1
fi

echo "==> Running Django database migrations..."
python manage.py migrate --noinput

echo "==> Collecting static assets..."
python manage.py collectstatic --noinput --clear || true

if [ "$SEED_DEMO" = "1" ] || [ "$SEED_DEMO" = "true" ]; then
    echo "==> Seeding rich demo dataset (Freelancer, Clients, Projects, Invoices)..."
    python manage.py seed_demo || true
fi

echo "==> Starting application server..."
exec "$@"
