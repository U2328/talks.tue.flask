#!/bin/sh

if [ ! -d postgres-backups ]; then
  mkdir -p postgres-backups;
fi

DUMP_FILE=${1:-"postgres-backups/$(ls postgres-backups | sort -r | head -1)"}
printf "Using dump file --> \033[36m%s\033[0m\n" $DUMP_FILE

if [ ! -f $DUMP_FILE ]; then
  printf "\033[31m!!! dump file not found\033[0m\n"
fi

docker-compose exec -u postgres db pg_restore -C -d postgres < $DUMP_FILE