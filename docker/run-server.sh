#!/bin/sh

. "`dirname $0`/container-settings.sh"

# This will start an ephemeral container for the Arrowhead service registry.
# The data will be linked from the data container
# Only the HTTP and CoAP frontends will be exposed, the DNS-SD service is only
# available within the container
#
# To expose the DNS service as well, add:
# -p 53:53/udp -p 53:53
# to the other flags below.
docker run --rm --volumes-from "${SERVICEREGISTRY_DATA_CONTAINER_NAME}" \
    -p 5683:5683/udp \
    "${SERVICEREGISTRY_CONTAINER_TAG}"
