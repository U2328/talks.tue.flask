# talks.tue
A webapp to manage talks and more at the Eberhard Karls University of Tübingen.

## Dependecies
1. [docker](https://www.docker.com/) for containerization
2. [docker-compose](https://github.com/docker/compose) for container orchastration

## Usage
1. run `make build` (this will take some time)
2. run `make run`

## Development
1. install [pipenv](https://pypi.org/project/pipenv/) and python 3.7.
2. run `make init_dev` (this will take some time)
3. run `make run`

## Creating a superuser
Simply run `make auth_createsuperuser` and fill out the prompts.

## Applying migrations
Run `make db_upgrade` and you should be golden.

## I messed up how can I fix this?
1. Don't panic
2. `make full_clean`
3. start over

## What else can `make` do for me?
Just run `make` and it will tell you. ;)
