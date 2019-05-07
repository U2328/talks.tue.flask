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
celery -A app.celery beat