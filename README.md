# SIGMOD25 NebulaStream NEEDMI Demo

## Build

 PULSE_COOKIE="" docker compose build

## Run

1. Ensure pulseaudio server is running on host with a valid audio source.
1. Set PULSE_COOKIE envvar as an absolute path, typically located at ~/.config/pulse/cookie
   `export PULSE_COOKIE=<FULL_PATH_TO_COOKIE>`
1. `docker-compose up`

