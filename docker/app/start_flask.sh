#!/bin/sh

echo "Waiting for postgres..."

while ! nc -z db 5432; do
  sleep 0.5
done

echo "Deploying DB"
flask deploy

echo "Starting server"
if [[ -z ${FLASK_DEBUG-0} ]]; then
  gunicorn -w 4 -u 1000 -b "0.0.0.0:5000" "app:create_app()"
else
  flask run -h "0.0.0.0" -p "5000"
fi