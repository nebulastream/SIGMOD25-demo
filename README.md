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

### Inspect Audio Stream

The raw audio stream comes from pulseaudio through a TCP socket.
As default, the samples come formatted as uint8 amplitude values in a bytestream.
No other information is transmitted in the stream.
It is possible to view this bytestream with netcat or socat on the port mapped in the compose file:
```
      - 22345:22345
```
```
$ nc localhost 22345
```

The current example query for the audio stream writes the stream to a csv inside of the container. 
This was done to show a query running successfully based on the configuration of the audio data source.
If leaving the compose environment running with this csv sink enabled, large amounts of storage may be consumed.
To see the csv file, connect with the worker container:
1. Find the container name `docker-compose ps`
2. Run bash as an interactive process inside of the container `docker exec -it $WORKER_CONTAINER_NAME /bin/bash`
3. List the files in the root folder `ll`
4. Audio.csv should be present and growing as the compose environment continues to run.

