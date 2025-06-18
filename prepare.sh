#!/usr/bin/env bash
# prepare.sh — discover host settings and write .env

cat > .env <<EOF
# host user/group mapped into the container:
HOST_UID=$(id -u)
HOST_GID=$(id -g)

# where Pulse stores its socket:
XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/$(id -u)}

# pick the first “input” source (your mic) by default:
PULSE_SOURCE=$(pactl get-default-source)
EOF

echo ".env written:"
cat .env

# rm containers
cd ../nebulastream-SIGMOD-demo/
sudo docker rm -vf $(sudo docker ps -aq) || true

# run nes
sudo docker run --rm --name nes -d --network=host -v $(pwd):$(pwd) -u root --workdir $(pwd) nebulastream/nes-development:video-demo ./cmake-build-release/nes-single-node-worker/nes-single-node-worker
