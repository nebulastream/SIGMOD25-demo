#!/usr/bin/env python3
import csv
import time
import sys
import signal
import warnings

import paho.mqtt.client as mqtt

# ─────────────── Workaround for large CSV fields ───────────────
csv.field_size_limit(sys.maxsize)               # allow arbitrarily large fields
warnings.filterwarnings(
    "ignore",
    message="Callback API version 1 is deprecated"
)
# ────────────────────────────────────────────────────────────────

# ─────────────── CONFIGURATION ───────────────
BROKER     = '192.168.1.104'    # your MQTT broker address
PORT       = 1883                  # your MQTT broker port
PUB_TOPIC  = 'test/serializer-image'   # where to publish the CSV‐lines
CSV_FILE   = 'test.csv'          # the file you generated earlier
# ───────────────────────────────────────────────

stop_requested = False

def signal_handler(sig, frame):
    global stop_requested
    print('\n← Interrupted, stopping replay…')
    stop_requested = True

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f'✔ Connected to {BROKER}:{PORT}, replaying {CSV_FILE} → "{PUB_TOPIC}"')
    else:
        print(f'❌ Connect failed (rc={rc})')
        sys.exit(1)

def main():
    global stop_requested
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 1. Connect & start background loop
    client = mqtt.Client()
    client.on_connect = on_connect
    try:
        client.connect(BROKER, PORT, keepalive=60)
    except Exception as e:
        print(f'❌ Could not connect to {BROKER}:{PORT}: {e}')
        sys.exit(1)
    client.loop_start()

    prev_ts = None

    # 2. Read & publish each CSV row, pacing by timestamp diff
    with open(CSV_FILE, 'r') as f:
        reader = csv.reader(f, delimiter=',', quoting=csv.QUOTE_NONE)
        for row in reader:
            if stop_requested:
                break

            # Expect exactly 5 columns
            try:
                timestamp_str, width, height, pix_fmt, img_b64 = row
            except ValueError:
                print(f'⚠ Skipping malformed row: {row}')
                continue

            # Parse nanosecond timestamp
            try:
                ts = int(timestamp_str)
            except ValueError:
                print(f'⚠ Invalid timestamp "{timestamp_str}", sending immediately')
                ts = None

            # Sleep for delta if we have a previous timestamp
            if prev_ts is not None and ts is not None:
                delta_s = (ts - prev_ts) / 1e9
                if delta_s > 0:
                    time.sleep(delta_s)

            # Rebuild and publish
            payload = ','.join([timestamp_str, width, height, pix_fmt, img_b64]) + '\n'
            rc = client.publish(PUB_TOPIC, payload)[0]
            if rc == mqtt.MQTT_ERR_SUCCESS:
                print(f'→ Published @ {timestamp_str}')
            else:
                print(f'⚠ Publish failed (rc={rc}) @ {timestamp_str}')

            prev_ts = ts

    # 3. Clean shutdown
    client.loop_stop()
    client.disconnect()
    print('✔ Replay complete, disconnected.')

if __name__ == '__main__':
    main()
