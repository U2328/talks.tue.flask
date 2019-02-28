# talks.tue
A webapp to manage talks and more at the Eberhard Karls University of Tübingen.

## Inital setup
1. install [pipenv](https://pypi.org/project/pipenv/) and make sure you can reach an installation of Python 3.7
2. run `make init`
3. run `make run`

## Dev Setup
Same as normal, just be sure to use `make init_dev` to install all the development dependecies.

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
