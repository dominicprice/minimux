#!/usr/bin/env bash

echo "active connections: $(( RANDOM % 5 ))"
echo "queries (last minute): $(( RANDOM % 100 ))"
echo "average latency: $(( RANDOM % 999))ms"
