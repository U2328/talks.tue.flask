.PHONY: help
mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
root_dir := $(dir $(mkfile_path))

help: ## view this help text
	@printf "\033[33m  ╔═══════════╗\033[0m\n"
	@printf "\033[33m  ║ talks.tue ║\033[0m\n"
	@printf "\033[33m  ╚═══════════╝\033[0m\n"
	@printf "\033[31m➥ All commands require running docker containers!\033[0m\n"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m ⇨ %s\n", $$1, $$2}'

auth_createsuperuser: ## create a superuser
	docker-compose exec app flask auth createsuperuser

babel_init: ## intialize new language
	docker-compose exec pybabel extract -F babel.cfg -k _l -o messages.pot .
	@read -p "locale:" locale; docker-compose exec pybabel init -i messages.pot -d app/translations -l $$locale
	rm messages.pot

babel_update: ## update all language files
	docker-compose exec pybabel extract -F babel.cfg -k _l -o messages.pot .
	docker-compose exec pybabel update -i messages.pot -d app/translations
	rm messages.pot

babel_compile: ## compile all language files
	docker-compose exec pybabel compile -d app/translations

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