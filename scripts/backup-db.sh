#!/bin/bash
docker compose down worker transcoder watchdog webapp frontend
set -o allexport; source .env; set +o allexport
cd /data/backups/db || exit
NOW_DATE=$(date +"%Y-%m-%d %T")
NOW_DATE_FN=$(echo $NOW_DATE |  tr '[: ]' '_') \
mysqldump timeline --result-file="timeline-${NOW_DATE_FN}-dump.sql" --host=localhost --port 3306 --user=root$DB_SUPER_USER --password=$DB_SUPER_USER_PW
docker compose up -d