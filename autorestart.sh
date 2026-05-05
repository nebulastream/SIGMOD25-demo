#!/bin/bash

# Path to your compose file (adjust if needed)
COMPOSE_FILE="./docker-compose.yml"

# Check every 2 seconds
INTERVAL=1

while true; do
  # List containers and check for failures
  failed=$(sudo docker compose ps -a | grep -e "unhealthy" -e "Exited" -e "exited" -e "dead")

  if [ -n "$failed" ]; then
    echo "$(date): Detected failed container(s): $failed"
    echo "Restarting worker..."
    sudo docker compose restart nes
  fi

  sleep $INTERVAL
done
