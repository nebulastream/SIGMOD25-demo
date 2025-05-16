# SIGMOD25 NebulaStream NEEDMI Demo

## prepare env variables
./prepare.sh

## build image and run container in the background
docker compose up --build --detach

## connect and see binary data
nc localhost 1234
## or write it into raw file
nc localhost 1234 > mic.raw
## then convert to audio file via ffmpeg
ffmpeg -f s16le -ar 48000 -ac 2 -i mic.raw mic.wav
