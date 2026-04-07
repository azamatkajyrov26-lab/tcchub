#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -q; do
    echo "PostgreSQL is not ready yet. Retrying in 2 seconds..."
    sleep 2
done
echo "PostgreSQL is ready."

echo "Waiting for Redis..."
REDIS_HOST="${REDIS_HOST:-redis}"
REDIS_PORT="${REDIS_PORT:-6379}"
until python -c "import redis; r=redis.Redis(host='$REDIS_HOST', port=$REDIS_PORT); r.ping()" 2>/dev/null; do
    echo "Redis is not ready yet. Retrying in 2 seconds..."
    sleep 2
done
echo "Redis is ready."

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Compiling translations..."
python manage.py compilemessages --ignore=.venv 2>/dev/null || true

exec "$@"
