#!/bin/bash
set -xeuo pipefail
docker-compose down
docker system prune -f
echo 1 > /proc/sys/vm/drop_caches
docker-compose build
docker-compose up -d