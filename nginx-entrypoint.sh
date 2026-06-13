#!/bin/sh
# Substitute DOMAIN env var into nginx config at container startup
DOMAIN=${DOMAIN:-localhost}
sed "s/__DOMAIN__/$DOMAIN/g" /etc/nginx/conf.d/proxy.conf.template > /etc/nginx/conf.d/default.conf
exec nginx -g "daemon off;"
