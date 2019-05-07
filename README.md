# talks.tue
A webapp to manage talks and more at the Eberhard Karls University of Tübingen.

## Dependecies
1. [docker](https://www.docker.com/) for containerization
2. [docker-compose](https://github.com/docker/compose) for container orchastration

## Deployment
1. make sure that your firewall has the proper rules set for HTTP and HTTPS
2. run `docker-compose build` (this will take some time)
3. run `docker-compose up`
4. open the [app](https://localhost) in your browser

## Development
1. install [pipenv](https://pypi.org/project/pipenv/) and python 3.7.
2. run `pipenv install --dev` (this can take some time)
3. set `DEBUG` in the `.env`-file to `1`
4. run `docker-compose build` (this will take some time)
5. run `docker-compose up`
6. open the [app](https://localhost) in your browser

### Note on security
In both cases Docker will be bound to the ports `80` and `443` on your machine. For deployment this is what we want, but in development it could be a security risk. Just make sure that your firewall is setup properly.

## Creating a superuser
Simply run `make auth_createsuperuser` and fill out the prompts.

## Applying migrations
Run `make db_upgrade` and you should be golden.

## What else can `make` do for me?
Just run `make` and it will tell you. ;)
