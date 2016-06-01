#!/bin/sh
# Start SimpleServiceRegistry
cd /opt/core-services/
mkdir -p /var/cache/arrowhead
chown servicedirectory /var/cache/arrowhead
chpst -u servicedirectory python3 ./sd_server.py -v 5 -f /var/cache/arrowhead/sd_server.blitzdb --http-bind 0.0.0.0 --http-port 8045 --coap-bind 0.0.0.0 --coap-port 5683
