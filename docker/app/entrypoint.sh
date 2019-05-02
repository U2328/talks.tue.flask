#!/bin/sh

echo "Waiting for postgres..."

while ! nc -z db 5432; do
  sleep 0.5
done

echo "Deploying DB"
flask deploy

echo "Starting server"
flask run --host=0.0.0.0