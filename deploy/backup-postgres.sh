#!/usr/bin/env sh
set -eu

backup_dir=${BACKUP_DIR:-/var/backups/jobda}
mkdir -p "$backup_dir"
timestamp=$(date +%Y%m%d-%H%M%S)
docker compose -f docker-compose.prod.yml exec -T postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > "$backup_dir/jobda-$timestamp.sql"
