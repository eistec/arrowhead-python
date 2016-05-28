#!/bin/sh

MACHINE_TYPE=`uname -m`
if [ x${MACHINE_TYPE} = xarmv7l ]; then
  # for ARM machines, use a different tag
  export SERVICEREGISTRY_CONTAINER_TAG=eistec/arrowhead-service-registry:armhf
else
  # default to x86
  export SERVICEREGISTRY_CONTAINER_TAG=eistec/arrowhead-service-registry:latest
fi

export SERVICEREGISTRY_DATA_CONTAINER_NAME=arrowhead-service-registry-store
