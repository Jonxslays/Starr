#!/bin/bash

# This script is used to start the Starr app.
# $1 and $2 are used to add --build -d if necessary.
echo "Starting the app"
docker-compose up $1 $2
echo "Done"
