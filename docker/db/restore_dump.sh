#!/bin/sh

if [ ! -d postgres-backups ]; then
  printf "\033[31m!!! no dump directory found, maybe no dumps were generated yet\033[0m\n"
  return 1
fi

DUMP_FILE=${1:-"postgres-backups/$(ls postgres-backups | sort -r | head -1)"}
printf "Using dump file --> \033[36m%s\033[0m\n" $DUMP_FILE

if [ ! -f $DUMP_FILE ]; then
  printf "\033[31m!!! dump file not found\033[0m\n"
fi

psql -d talks_tue -U postgres -f $DUMP_FILE