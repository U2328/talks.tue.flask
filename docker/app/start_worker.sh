#!/bin/sh

set -o errexit
set -o pipefail
set -o nounset

echo "Starting celery worker"
if [[ -z ${DEBUG-0} ]]; then
    celery -A app.celery worker --uid 1000
else
    watchmedo auto-restart -d /code -p '*.py' -- celery -A app.celery worker --uid 1000
fi