#!/bin/bash

# This script is used to restart the app.
# $1 and $2 are used to add --build -d if necessary.
./scripts/kill.sh && ./scripts/start.sh $1 $2
