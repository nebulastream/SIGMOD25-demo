#!/usr/bin/env bash
# prepare.sh — discover host settings and write .env

source ./patient-monitor/live/prepare_patient_monitor.env

# auto-detect local IP
LOCAL_IP=$(hostname -I | awk '{print $1}')

cat > .env <<EOF
# host user/group mapped into the container:
HOST_UID=$(id -u)
HOST_GID=$(id -g)

# where Pulse stores its socket:
XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/$(id -u)}

# pick the first “input” source (your mic) by default:
PULSE_SOURCE=$(pactl get-default-source)
### envvars for patient monitor
# the IP of the jumphost
JUMP_HOST=${JUMP_HOST}

# the IP of the local machine running docker-compose
LOCAL_IP=${LOCAL_IP}

USB_DEV=${USB_DEV}
### end of envvars for patient monitor
EOF

echo ".env written:"
cat .env

# substitute env vars and create start_payload_generated.json
export LOCAL_IP USB_DEV JUMP_HOST
envsubst < patient-monitor/live/start_payload.json.template > patient-monitor/live/start_payload_generated.json

# rm containers
cd ../nebulastream-SIGMOD-demo/
sudo docker rm -vf $(sudo docker ps -aq) || true

# run nes
# sudo docker run --name nes -d --network=host -v $(pwd):$(pwd) -u root --workdir $(pwd) nebulastream/nes-development:video-demo ./cmake-build-release/nes-single-node-worker/nes-single-node-worker

