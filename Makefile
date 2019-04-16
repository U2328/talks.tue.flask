.PHONY: help
mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
root_dir := $(dir $(mkfile_path))

help: ## view this help text
	@echo '  /-----------\'
	@echo '  | talks.tue |'
	@echo '  \-----------/'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

init: ## init the whole env
	pipenv install --skip-lock
	$(MAKE) db_deploy

init_dev: ## init the whole env for dev
	pipenv install --dev --pre
	$(MAKE) db_deploy

re_init: ## reinitialize the whole env
	$(MAKE) clean_env;
	$(MAKE) init;

re_init_dev: ## reinitialize the whole dev env
	$(MAKE) clean_env;
	$(MAKE) init_dev;

run: ## run the webserver
	pipenv run flask run

auth_createsuperuser: ## create a superuser
	pipenv run flask auth createsuperuser

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

lint: ## run linters on project files (dev only)
	pipenv run flake8

db_reset: ## reset database
	$(MAKE) clean_db
	$(MAKE) db_deploy

db_migrate: ## generate database-migration
	pipenv run flask db migrate

db_upgrade: ## upgrade database
	pipenv run flask db upgrade

db_migration: ## find out what the current db revision is
	pipenv run flask db show

db_migrations: ## list all known migrations
	pipenv run flask db history

db_deploy: ## init server setup
	pipenv run flask deploy

clean_db: ## remove db files
	find . -type f -name '*.db' -exec rm {} \;

clean_env: ## remove python env
	pipenv --rm;

clean_cache: ## remove cached files
	find $(root_dir) -type f -name '*.pyc' -exec rm {} \;
	find $(root_dir) -type d -name '__pycache__' -exec rmdir {} \;

full_clean: ## cleanup everything
	$(MAKE) clean_cache;
	$(MAKE) clean_db;
	$(MAKE) clean_env;