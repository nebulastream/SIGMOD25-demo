FROM nebulastream/worker:audio-inference
ADD data/audio.csv /audio.csv
RUN apt-get update -y && apt-get install -y \
    lsof
