#!/bin/sh
# wait-for-db.sh

set -e

host="$DB_HOST"
port="$DB_PORT"

until nc -z "$host" "$port"; do
  echo "Waiting for database at $host:$port..."
  sleep 1
done

echo "Database is up!"

# Run migrations
python manage.py migrate --noinput
# Collect static files (optional)
python manage.py collectstatic --noinput

# Run the main process
exec "$@"
