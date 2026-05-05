#!/usr/bin/env bash

sudo docker compose down -t 0

./prepare.sh

sudo docker compose up -d