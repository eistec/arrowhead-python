#!/bin/sh

MACHINE_TYPE=`uname -m`
if [ x${MACHINE_TYPE} = xarmv7l ]; then
  # for ARM machines, use a different tag
  export SERVICEREGISTRY_CONTAINER_TAG=eistec/arrowhead-servicedirectory:armhf
else
  # default to x86
  export SERVICEREGISTRY_CONTAINER_TAG=eistec/arrowhead-servicedirectory:latest
fi

export SERVICEREGISTRY_DATA_CONTAINER_NAME=arrowhead-servicedirectory-store
