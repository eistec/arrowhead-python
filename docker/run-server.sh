#!/bin/sh

. "`dirname $0`/container-settings.sh"

# This will start an ephemeral container for the Arrowhead service registry.
# The data will be linked from the data container
docker run --rm --volumes-from "${SERVICEREGISTRY_DATA_CONTAINER_NAME}" \
    -p 8045:8045 \
    -p 5683:5683/udp \
    "${SERVICEREGISTRY_CONTAINER_TAG}"
