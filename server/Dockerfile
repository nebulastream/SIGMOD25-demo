FROM ubuntu:24.04

ADD server/microphone-server.py microphone-server.py

RUN apt-get update && apt-get install -y \
    libasound-dev \
    portaudio19-dev \
    libportaudio2 \
    libportaudiocpp0 \
    ffmpeg \
    alsa-utils
RUN apt-get install python3-pyaudio && rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["python3", "microphone-server.py"]
