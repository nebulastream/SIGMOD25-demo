import sys
import time
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
    section = "spo2_arsd"
    for arg in sys.argv[1:]:
        if arg.startswith("CONF="):
            section = arg.split("=", 1)[1]
    if section == "":
        raise Exception("No config given")

    cfg = load_cfg()
    spo2_cfg = cfg.get(section, {})

    BROKER_HOST = spo2_cfg.get("broker", "localhost")
    BROKER_PORT = spo2_cfg.get("port", 1883)
    TOPIC = spo2_cfg.get("topic", "patientMonitorReplay/SpO2")
    PUBLISH_PERIOD_MICROSECS = int(spo2_cfg.get("period", 300_000))
    START_EPOCH = int(spo2_cfg.get("start_epoch", 1735772400000000))  # microseconds
    CYCLE_DURATION_MICROSECS = int(spo2_cfg.get("full_cycle_duration", 10_000_000))
    SPO2_VALUES = spo2_cfg.get("spo2_values", [98, 90])
    INIT_PHASE = int(spo2_cfg.get("init_phase_duration", 300_000_000))
    TRANSITION_PHASE = int(spo2_cfg.get("phase_over_duration", 200_000_000))

    if len(SPO2_VALUES) != 2:
        raise ValueError("spo2_values must contain exactly 2 values")

    normal, sick = SPO2_VALUES
    sick_phase = CYCLE_DURATION_MICROSECS - (INIT_PHASE + TRANSITION_PHASE)

    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.loop_start()

    try:
        while True:
            now_ms = int(time.time() * 1_000_000)
            elapsed = (now_ms - START_EPOCH) % CYCLE_DURATION_MICROSECS

            if elapsed < INIT_PHASE:
                value = normal
            elif elapsed < INIT_PHASE + TRANSITION_PHASE:
                ratio = (elapsed - INIT_PHASE) / TRANSITION_PHASE
                value = interpolate(normal, sick, ratio)
            else:
                value = sick

            msg = f"{now_ms},{value}|"
            client.publish(TOPIC, msg, qos=1)

            next_tick_ms = START_EPOCH + ((now_ms - START_EPOCH) // PUBLISH_PERIOD_MICROSECS + 1) * PUBLISH_PERIOD_MICROSECS
            sleep_time = max(0, (next_tick_ms - int(time.time() * 1_000_000)) / 1_000_000)
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\n[×] Stopping publisher...")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
