.PHONY: help
mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
root_dir := $(dir $(mkfile_path))

help: ## view this help text
	@echo '  /-----------\'
	@echo '  | talks.tue |'
	@echo '  \-----------/'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

build: ## build docker images
	docker-compose build

init_dev: ## init the whole env for dev
	$(MAKE) build
	pipenv install --dev --pre

run: ## run the webserver
	docker-compose up

auth_createsuperuser: ## create a superuser
	docker-compose exec app flask auth createsuperuser

babel_init: ## intialize new language
	pipenv run pybabel extract -F babel.cfg -k _l -o messages.pot .
	@read -p "locale:" locale; pipenv run pybabel init -i messages.pot -d app/translations -l $$locale
	rm messages.pot

babel_update: ## update all language files
	pipenv run pybabel extract -F babel.cfg -k _l -o messages.pot .
	pipenv run pybabel update -i messages.pot -d app/translations
	rm messages.pot

babel_compile: ## compile all language files
	pipenv run pybabel compile -d app/translations

db_migrate: ## generate database-migration
	docker-compose exec app flask db migrate

db_apply: ## apply database-migration
	docker-compose exec app flask db apply

db_migration: ## find out what the current db revision is
	docker-compose exec app flask db show

db_migrations: ## list all known migrations
	docker-compose exec app flask db history

db_deploy: ## init server setup
	docker-compose exec app flask deploy

clean_cache: ## remove cached files
	find $(root_dir) -type f -name '*.pyc' -exec rm {} \;
	find $(root_dir) -type d -name '__pycache__' -exec rmdir {} \;

clean_env: ## remove pipenv env
	pipenv --rm;

clean_docker: ## remove docker containers
	docker-compose kill;
	docker-compose rm;

full_clean: ## apply all other cleans
	$(MAKE) clean_cache clean_env clean_docker