.PHONY: help
mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
root_dir := $(dir $(mkfile_path))

help: ## view this help text
	@echo '  /-----------\'
	@echo '  | talks.tue |'
	@echo '  \-----------/'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

init: ## init the whole env
	pipenv install
	$(MAKE) auto_upgrade
	$(MAKE) deploy

init_dev: ## init the whole env for dev
	pipenv install --dev
	$(MAKE) auto_upgrade
	$(MAKE) deploy

migrate: ## generate database-migration
	pipenv run flask db migrate

upgrade: ## upgrade database
	pipenv run flask db upgrade

auto_upgrade: ## migrate + upgrade
	$(MAKE) migrate
	$(MAKE) upgrade

current_migration: ## find out what the current db revision is
	pipenv run flask db show

list_migrations: ## list all known migrations
	pipenv run flask db history

clean_db: ## remove db files
	find -type f -name *.db -exec rm {} \;

clean_cache: ## remove cached files
	find -type f -name *.pyc -exec rm {} \;
	find $(root_dir) -type d -name __pycache__ -exec rmdir {} \;

full_clean: ## cleanup everythin
	$(MAKE) clean_cache
	$(MAKE) clean_db
	pipenv --rm

run: ## run the webserver
	pipenv run flask run

deploy: ## init server setup
	pipenv run flask deploy

createsuperuser: ## create a superuser
	pipenv run flask auth createsuperuser

babel_init: ## intialize new language
	pipenv run flask translate init

babel_update: ## update all language files
	pipenv run flask translate update

babel_compile: ## compile all language files
	pipenv run flask translate compile