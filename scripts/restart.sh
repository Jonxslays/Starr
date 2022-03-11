#!/bin/bash

# This script is used to restart the app.
# $1 is used to add --build if necessary.
./scripts/kill.sh && ./scripts/start.sh $1 $2
