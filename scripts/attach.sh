#!/bin/bash

# This script is used to attach to the running docker container via shell.
CONTAINER=$(docker ps | grep starr_starr-app | awk '{print $1}')

echo "Attaching to $CONTAINER"
docker container exec -it $CONTAINER /bin/bash
echo "Connection closed"
