#!/bin/bash

# This script is used to attach to the running docker
# container via shell. $1 should be the container name.
CONTAINER=$(docker ps | grep $1 | awk '{print $1}')

echo "Attaching to $CONTAINER"
docker container exec -it $CONTAINER /bin/bash
echo "Connection closed"
