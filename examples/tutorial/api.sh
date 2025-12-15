#!/usr/bin/env bash

echo "Starting the api..."

while true; do
	echo "$(date) handling request..."
	sleep "$(( (RANDOM % 5) + 2 ))s"
done
