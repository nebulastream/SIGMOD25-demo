#!/usr/bin/env bash
# prepare.sh — discover host settings and write .env

read -p "Enter the jump host IP: " JUMP_HOST

read -p "Enter the USB device path that the Patient Monitor is connected to on the jump host! [press enter for default: /dev/ttyUSB0]: " USB_DEV
USB_DEV=${USB_DEV:-/dev/ttyUSB0}

# auto-detect local IP
LOCAL_IP=$(ip route get 1 | awk '{print $NF; exit}')

cat > .env <<EOF
# host user/group mapped into the container:
HOST_UID=$(id -u)
HOST_GID=$(id -g)

# where Pulse stores its socket:
XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/$(id -u)}

# pick the first “input” source (your mic) by default:
PULSE_SOURCE=$(pactl info \
  | awk -F": " '/Default Source/ { print $2 }')

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
