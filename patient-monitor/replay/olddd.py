import sys, time, random
from pathlib import Path
import yaml, paho.mqtt.client as mqtt


# ── helpers ──────────────────────────────────────────────────────────────────
def load_cfg(path="config.yml"):
    p = Path(path)
    return yaml.safe_load(p.read_text()) if p.is_file() else {}


def on_connect(c, u, f, rc, p=None):
    print("[✓] Connected" if rc == 0 else f"[!] Connection failed ({rc=})")


def lerp(a, b, r):          # linear interpolation
    return round(a + (b - a) * r)


# ── generator ────────────────────────────────────────────────────────────────
def run(cfg):
    #   MQTT ---------------------------------------------------------------
    host = cfg.get("broker", "localhost")
    port = cfg.get("port", 1883)
    topic = cfg.get("topic", "patientMonitorReplay/Signal")

    cli = mqtt.Client()
    cli.on_connect = on_connect
    cli.connect(host, port, 60)
    cli.loop_start()

    #   time base ----------------------------------------------------------
    start_epoch_cfg = int(cfg.get("start_epoch", 0))
    unit_cfg        = str(cfg.get("timestamp_unit", "")).lower()

    if unit_cfg in {"us", "ns"}:
        unit = unit_cfg
    else:
        unit = "ns" if start_epoch_cfg > 1e14 else "us"   # auto-detect

    BASE = 1_000_000 if unit == "us" else 1_000_000_000  # units / second
    start_epoch = start_epoch_cfg if unit == "ns" else start_epoch_cfg

    period_s       = float(cfg.get("period", 1.0))
    step           = int(period_s * BASE)                # units / tick
    cycle          = int(cfg.get("full_cycle_duration", 10) * BASE)
    init_phase     = int(cfg.get("init_phase_duration", 3) * BASE)
    trans_phase    = int(cfg.get("phase_over_duration", 2) * BASE)

    vals           = cfg.get("values", [100, 60])
    var_rng        = int(cfg.get("variation", 0))
    if len(vals) != 2:
        raise ValueError("values must contain [normal, sick]")
    normal, sick = vals

    tick, deadline = 0, time.time()

    try:
        while True:
            ts = start_epoch + tick * step

            # value generation -------------------------------------------
            elapsed = (ts - start_epoch) % cycle
            if elapsed < init_phase:
                val = normal
            elif elapsed < init_phase + trans_phase:
                val = lerp(normal, sick, (elapsed - init_phase) / trans_phase)
            else:
                val = sick
            if var_rng:
                val = max(0, val + random.randint(-var_rng, var_rng))

            cli.publish(topic, f"{ts},{val}|", qos=1)

            tick += 1
            deadline += period_s
            time.sleep(max(0.0, deadline - time.time()))

    except KeyboardInterrupt:
        print("\n[×] Stopping generator…")
    finally:
        cli.loop_stop(); cli.disconnect()


# ── entry point ─────────────────────────────────────────────────────────────
def main():
    section = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("CONF=")), "")
    if not section:
        raise SystemExit("Usage: generator.py CONF=<config-section>")
    run(load_cfg().get(section, {}))


if __name__ == "__main__":
    main()

