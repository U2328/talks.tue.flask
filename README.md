# talks.tue
A webapp to manage talks and more at the Eberhard Karls University of Tübingen.

## Inital setup
1. install [pipenv](https://pypi.org/project/pipenv/)
2. run `make init`
3. run `make run`

## Dev Setup
Same as normal, just be sure to use `make init_dev` to install all the development dependecies.

## Creating a superuser
Simply run `make createsuperuser` and fill out the prompts.

## Applying migrations
Run `make upgrade` and you should be golden.

## I messed up how can I fix this?
1. Don't panic
2. `make full_clean`
3. start over
