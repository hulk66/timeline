#!/usr/bin/env sh
set -eu

envsubst '${BE_HOST} ${BE_PORT}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

exec "$@"