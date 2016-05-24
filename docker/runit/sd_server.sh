#!/bin/sh
# Start SimpleServiceRegistry
cd /opt/core-services/
chpst -u servicedirectory python3 ./sd_server.py
