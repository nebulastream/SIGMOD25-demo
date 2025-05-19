# SIGMOD25 NebulaStream NEEDMI Demo

This repository is an effort to bring all the work for each modality together, and make everything easy-to-run with a few commands.

## Build

Run the prepare script to set environment variables: `./prepare.sh`

## Run

Run the setup with:
```
docker compose up --build --force-recreate
```

## Shutting-down

It is recommended to use `docker compose down` to remove containers before next run.

