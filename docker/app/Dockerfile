FROM python:3.7-alpine

# Copy project
ADD . /code
WORKDIR /code

# Install dependencies
RUN apk update && apk upgrade
RUN apk add --update --no-cache g++ gcc libxslt-dev netcat-openbsd &&\
    apk add postgresql-dev python3-dev musl-dev libffi-dev
RUN pip install pipenv psycopg2 gunicorn
RUN pipenv install --system --deploy --ignore-pipfile

# Add non-su user
RUN adduser -D -g '' -u 1000 talks_tue

# command set in docker-compose