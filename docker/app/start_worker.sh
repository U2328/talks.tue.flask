#!/bin/sh

set -o errexit
set -o pipefail
set -o nounset

echo "Waiting for rabbitmq..."
while ! nc -z rabbit 5672; do
  sleep 0.5
done

echo "Starting celery worker"
if [[ ${FLASK_DEBUG-0} -eq 0 ]]; then
    celery -A app.celery worker --uid 1000
else
    watchmedo auto-restart -d /code -p '*.py' -- celery -A app.celery worker --uid 1000
fi