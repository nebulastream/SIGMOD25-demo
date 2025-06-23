#!/usr/bin/env bash

# rm containers
cd ../nebulastream-SIGMOD-demo/
sudo docker rm -vf $(sudo docker ps -aq) || true

# run nes
sudo docker run --rm --name nes -d --network=host -v $(pwd):$(pwd) -u root --workdir $(pwd) nebulastream/nes-development:video-demo ./cmake-build-release/nes-single-node-worker/nes-single-node-worker
