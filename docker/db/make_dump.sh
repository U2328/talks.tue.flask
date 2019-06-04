#!/bin/sh

if [ ! -d postgres-backups ]; then
  mkdir -p postgres-backups;
fi

FORMATED_TIME=$(date +'%Y-%m-%d_%H%M%S')
DUMP_FILE="postgres-backups/$FORMATED_TIME.dump.gz"

pg_dump -Fc -U postgres talks_tue > $DUMP_FILE
printf "Generated dump file --> \033[36m%s\033[0m\n" $DUMP_FILE