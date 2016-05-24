#!/bin/sh
# Start SimpleServiceRegistry
cd /opt/core-services/
mkdir -p /var/cache/arrowhead
touch /var/cache/arrowhead/servicedirectory_db.json
chown servicedirectory /var/cache/arrowhead/servicedirectory_db.json
chpst -u servicedirectory python3 ./sd_server.py -v 5 -f /var/cache/arrowhead/servicedirectory_db.json
