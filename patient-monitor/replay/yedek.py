import sys
import time
import random
from pathlib import Path

import paho.mqtt.client as mqtt
import yaml


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def load_cfg(path: str | Path = "config.yml") -> dict:
    """Load the YAML config file (empty dict if missing)."""
    p = Path(path)
    if p.is_file():
        with p.open() as f:
            return yaml.safe_load(f) or {}
    return {}


def on_connect(client, userdata, flags, rc, properties=None):
    print("[✓] Connected" if rc == 0 else f"[!] Connection failed (rc={rc})")


def interpolate(start: int, end: int, ratio: float) -> int:
    """Linear interpolation, rounded to an int."""
    return round(start + (end - start) * ratio)


# ──────────────────────────────────────────────────────────────────────────────
# Generator
# ──────────────────────────────────────────────────────────────────────────────
def run_generator(cfg: dict):
    # ── MQTT connection settings ────────────────────────────────────────────
    BROKER_HOST = cfg.get("broker", "localhost")
    BROKER_PORT = cfg.get("port", 1883)
    TOPIC       = cfg.get("topic", "patientMonitorReplay/Signal")

    # ── Timing parameters (all in µs) ───────────────────────────────────────
    PUBLISH_PERIOD = int(cfg.get("period", 1.0) * 1_000_000)        # default 1 s
    START_EPOCH    = int(cfg.get("start_epoch", 1735772400000000))  # µs since 1970-01-01

    CYCLE_DURATION   = int(cfg.get("full_cycle_duration", 10) * 1_000_000)
    INIT_PHASE       = int(cfg.get("init_phase_duration", 3) * 1_000_000)
    TRANSITION_PHASE = int(cfg.get("phase_over_duration", 2) * 1_000_000)

    # ── Value generation parameters ─────────────────────────────────────────
    VALUES    = cfg.get("values", [100, 60])
    VARIATION = int(cfg.get("variation", 0))

    if len(VALUES) != 2:
        raise ValueError("`values` must contain exactly two numbers [normal, sick]")

    normal, sick = VALUES

    # ── MQTT client setup ───────────────────────────────────────────────────
    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.loop_start()

    # ── Time-keeping for the loop ───────────────────────────────────────────
    tick          = 0                         # number of messages already sent
    next_deadline = time.time()               # wall-clock time for tick 0

    try:
        while True:
            # 1) Simulated timestamp (µs) that starts at START_EPOCH and
            #    moves forward by exactly PUBLISH_PERIOD each loop
            msg_timestamp = START_EPOCH + tick * PUBLISH_PERIOD

            # 2) Determine phase within one cycle to pick / interpolate value
            elapsed = (msg_timestamp - START_EPOCH) % CYCLE_DURATION
            if elapsed < INIT_PHASE:
                value = normal
            elif elapsed < INIT_PHASE + TRANSITION_PHASE:
                ratio = (elapsed - INIT_PHASE) / TRANSITION_PHASE
                value = interpolate(normal, sick, ratio)
            else:
                value = sick

            if VARIATION > 0:
                #value += random.randint(-VARIATION, VARIATION)
                #value = max(0, value)
                value += VARIATION

            # 3) Publish
            client.publish(TOPIC, f"{msg_timestamp},{value}|", qos=1)

            # 4) Schedule next iteration
            tick += 1
            next_deadline += PUBLISH_PERIOD / 1_000_000  # convert µs → seconds
            sleep_s = next_deadline - time.time()
            if sleep_s > 0:
                time.sleep(sleep_s)

    except KeyboardInterrupt:
        print("\n[×] Stopping generator…")
    finally:
        client.loop_stop()
        client.disconnect()


# ──────────────────────────────────────────────────────────────────────────────
# Entrypoint
# ──────────────────────────────────────────────────────────────────────────────
def main():
    section = ""
    for arg in sys.argv[1:]:
        if arg.startswith("CONF="):
            section = arg.split("=", 1)[1]
    if not section:
        raise SystemExit("No config section specified (use CONF=<section>)")

    cfg = load_cfg().get(section, {})
    run_generator(cfg)


if __name__ == "__main__":
    main()
