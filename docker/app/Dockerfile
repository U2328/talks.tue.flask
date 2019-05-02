FROM python:3.7-alpine

# Copy project
ADD . /code
WORKDIR /code

# Install dependencies
RUN apk update && apk upgrade
RUN apk add --update --no-cache g++ gcc libxslt-dev netcat-openbsd &&\
    apk add postgresql-dev python3-dev musl-dev
RUN pip install pipenv psycopg2
RUN pipenv install --system --deploy --ignore-pipfile

CMD [ "sh", "docker/app/entrypoint.sh" ]