import sys
import time
import random
import paho.mqtt.client as mqtt
import yaml
from pathlib import Path


def load_cfg(path: str | Path = "config.yml") -> dict:
    p = Path(path)
    if p.is_file():
        with p.open() as f:
            return yaml.safe_load(f) or {}
    return {}


def on_connect(client, userdata, flags, rc, properties=None):
    print("[✓] Connected" if rc == 0 else f"[!] Connection failed (rc={rc})")


def interpolate(start, end, ratio):
    return round(start + (end - start) * ratio)


def main():
    section = ""
    for arg in sys.argv[1:]:
        if arg.startswith("CONF="):
            section = arg.split("=", 1)[1]
    if section == "":
        raise Exception("No config given")

    cfg = load_cfg()
    hr_cfg = cfg.get(section, {})

    BROKER_HOST = hr_cfg.get("broker", "localhost")
    BROKER_PORT = hr_cfg.get("port", 1883)
    TOPIC = hr_cfg.get("topic", "patientMonitorReplay/HR")
    PUBLISH_PERIOD_MICROSECS = int(hr_cfg.get("period", 0.3) * 1_000_000)
    START_EPOCH = int(hr_cfg.get("start_epoch", 1735772400000000))  # µs
    CYCLE_DURATION_MICROSECS = int(hr_cfg.get("full_cycle_duration", 10) * 1_000_000)
    HEART_RATES = hr_cfg.get("heart_rates", [80, 120])
    INIT_PHASE = int(hr_cfg.get("init_phase_duration", 3) * 1_000_000)
    TRANSITION_PHASE = int(hr_cfg.get("phase_over_duration", 2) * 1_000_000)

    if len(HEART_RATES) != 2:
        raise ValueError("heart_rates must contain exactly 2 values")

    normal, sick = HEART_RATES
    sick_phase = CYCLE_DURATION_MICROSECS - (INIT_PHASE + TRANSITION_PHASE * 2)
    VARIATION = 1

    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.loop_start()

    try:
        while True:
            now_us = int(time.time() * 1_000_000)
            elapsed = (now_us - START_EPOCH) % CYCLE_DURATION_MICROSECS

            if elapsed < INIT_PHASE:
                value = normal
            elif elapsed < INIT_PHASE + TRANSITION_PHASE:
                # Transition from normal to sick
                ratio = (elapsed - INIT_PHASE) / TRANSITION_PHASE
                value = interpolate(normal, sick, ratio)
            else:
                value = sick

            variation = random.randint(-VARIATION, VARIATION)
            value = max(0, value + variation)

            msg = f"{now_us},{value}|"
            client.publish(TOPIC, msg, qos=1)

            next_tick_us = START_EPOCH + ((now_us - START_EPOCH) // PUBLISH_PERIOD_MICROSECS + 1) * PUBLISH_PERIOD_MICROSECS
            sleep_time = max(0, (next_tick_us - int(time.time() * 1_000_000)) / 1_000_000)
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\n[×] Stopping publisher...")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
