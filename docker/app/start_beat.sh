#!/bin/sh

set -o errexit
set -o pipefail
set -o nounset
rm celerybeat.pid -f

echo "Starting celery beat"
celery -A app.celery beat