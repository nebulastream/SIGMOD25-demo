import neurokit2 as nk
import numpy as np
import time
from datetime import datetime, timezone
import paho.mqtt.client as mqtt
import yaml
from pathlib import Path
from newecg import SignalBuffer, PeriodicSignalHandler, remap

def load_cfg(path: str | Path = "config.yml") -> dict:
  p = Path(path)
  if p.is_file():
    with p.open() as f:
      return yaml.safe_load(f) or {}
  return {}

def generate_data():
  fps = 50
  sample_rate = 180
  x_window = 3 #seconds
  slide_duration = 1 # seconds
  simulated_ecg = nk.ecg_simulate(duration=8, sampling_rate=200, heart_rate=80)
  simulated_ecg = nk.ecg_simulate(duration=2, sampling_rate=sample_rate, method="daubechies", heart_rate=60, heart_rate_std=0)
  tile = simulated_ecg[0:sample_rate]
  tile_count = (x_window * sample_rate) + (slide_duration * sample_rate)
  simulated_ecg = np.tile(tile,tile_count)
  print(np.shape(simulated_ecg))
  return simulated_ecg

def on_connect(client, userdata, flags, rc, properties=None):
  print("[✓] Connected" if rc == 0 else f"[!] Connection failed (rc={rc})")

def on_publish(client, userdata, mid):
  print(f"CSV message {mid} published")

def main() -> None:

  cfg = yaml.safe_load(Path("config.yml").read_text()) or {}
  ecg_cfg = cfg.get("ecg", {})

  BROKER_HOST    = ecg_cfg.get("broker", "localhost")
  BROKER_PORT    = ecg_cfg.get("port", 1882)
  TOPIC          = ecg_cfg.get("topic", "sink/live/patient_monitor_ecg_value")
  PUBLISH_PERIOD = ecg_cfg.get("period", 30) # in ms

  # data = generate_data()
  count = 20
  min_freq = 20
  max_freq = 120
  update_width = 0.5

  # Assuming you have the SignalBuffer class and helper functions defined
  signal_buffer = SignalBuffer.precompute(
    count,
    lambda i: nk.ecg_simulate(duration=1,sampling_rate=1000,heart_rate=remap(i, 0, count - 1, min_freq, max_freq))
  )
  index = 0

  signal_handler = PeriodicSignalHandler(signal_buffer)

  client = mqtt.Client()
  client.on_connect = on_connect
  #client.on_publish = on_publish

  client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
  client.loop_start()

  signal_handler.reset_signal()

  try:
    while True:
      timestamp = int(datetime.now(timezone.utc).timestamp() * 1_000)

      csv_row = f"{timestamp},{data[index]}|"

      #client.publish(TOPIC, csv_row, qos=1, retain=False)
      print(signal_handler.get_signal())

      index = (index + 1) % len(data)

      time.sleep(PUBLISH_PERIOD/1000)

  except KeyboardInterrupt:
    print("\n[×] Stopping publisher...")
  finally:
    client.loop_stop()
    client.disconnect()

if __name__ == "__main__":
  main()
