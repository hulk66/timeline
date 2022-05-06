#!/usr/bin/env sh
set -eu

envsubst '${BE_HOST} ${BE_PORT} ${TIMELINE_BASEPATH}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

exec "$@"