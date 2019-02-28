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

db_migrate: ## generate database-migration
	pipenv run flask db migrate

db_upgrade: ## upgrade database
	pipenv run flask db upgrade

db_auto_upgrade: ## migrate + upgrade
	$(MAKE) db_migrate
	$(MAKE) db_upgrade

db_current_migration: ## find out what the current db revision is
	pipenv run flask db show

db_list_migrations: ## list all known migrations
	pipenv run flask db history

clean_db: ## remove db files
	find . -type f -name '*.db' -exec rm {} \;

clean_cache: ## remove cached files
	find $(root_dir) -type f -name '*.pyc' -exec rm {} \;
	find $(root_dir) -type d -name '__pycache__' -exec rmdir {} \;

full_clean: ## cleanup everythin
	$(MAKE) clean_cache
	$(MAKE) clean_db
	pipenv --rm

run: ## run the webserver
	pipenv run flask run

db_deploy: ## init server setup
	pipenv run flask deploy

auth_createsuperuser: ## create a superuser
	pipenv run flask auth createsuperuser

babel_init: ## intialize new language
	pipenv run flask translate init

babel_update: ## update all language files
	pipenv run flask translate update

babel_compile: ## compile all language files
	pipenv run flask translate compile

lint: ## run linters on project files (dev only)
	pipenv run flake8