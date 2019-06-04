FROM postgres:11.2-alpine

ADD . /code

# run create.sql on init
ADD create.sql /docker-entrypoint-initdb.d