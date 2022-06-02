#!/usr/bin/env sh
set -eu

envsubst '${BE_HOST} ${BE_PORT} ${TIMELINE_BASEPATH}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

SRC=/app/config.js
NEW_CONFIG="$(./create_config_js.sh $SRC)"
echo "$NEW_CONFIG" > $SRC


exec "$@"