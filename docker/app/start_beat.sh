#!/bin/sh

set -o errexit
set -o pipefail
set -o nounset
rm celerybeat.pid -f

echo "Waiting for rabbitmq..."
while ! nc -z rabbit 5672; do
  sleep 0.5
done

echo "Starting celery beat"
if [[ ${FLASK_DEBUG-0} -eq 0 ]]; then
    celery -A app.celery beat --uid 1000
else
    watchmedo auto-restart -d /code -p 'app/config.py;app/celery.py;app/tasks.py' -- celery -A app.celery beat --uid 1000
fi