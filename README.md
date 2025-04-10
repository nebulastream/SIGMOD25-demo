# SIGMOD25 NebulaStream NEEDMI Demo

## Build

1. Ensure pulseaudio server is running on host. `pactl info`
1. Copy your PULSE_COOKIE to ./audio-simple-tcp/ (It is typically found at ~/.config/pulse/cookie)
   `cp ~/.config/pulse/cookie ./audio-simple-tcp/cookie`
1. `docker-compose build` or if not using standalone `docker compose build`

## Run

Note: The audio containers do not play nice with rootless docker. Run with a rooted daemon to avoid issues with the audio container failing to build a tunnel to the pulse-audio server of the host machine.

1. Ensure pulseaudio server is running on host with a valid audio source. `pactl list sources short`
1. `docker-compose up` or if not using standalone `docker compose up`

