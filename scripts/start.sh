#!/bin/bash

# This script is used to start the Starr app.
# $1 is used to add --build if necessary.
echo "Starting the app"
docker-compose up -d $1
echo "Done"
