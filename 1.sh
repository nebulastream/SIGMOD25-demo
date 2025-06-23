#!/usr/bin/env bash

sudo docker compose -f compose-shock.yml down -t 0
sudo docker compose down -t 0

./prepare.sh

sudo docker compose up -d