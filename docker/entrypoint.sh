#!/bin/bash
set -e # exit when error occur

# database setting
echo "waiting for database..."
until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c '\q'; do
  sleep 2
done
# database migrate
python manage.py migrate

# execute COMMAND
exec "$@"
