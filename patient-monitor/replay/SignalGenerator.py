from datetime import datetime, timezone
import numpy as np
import paho.mqtt.client as mqtt
from typing import Callable
import time
import yaml

from newecg import SignalBuffer, PeriodicSignalHandler, remap

class SignalGenerator:

    def __init__(self, settings: dict):
        self.broker_host = settings["borker_host"]
        self.broker_port = settings["borker_port"]
        self.publish_topic = settings["publish_topic"]
        self.publish_period = settings["publish_period"]/1000
        self.generation_min = settings["generation_min"]
        self.generation_max = settings["generation_max"]
        self.generation_count = settings["generation_count"]
        self.subscribe_topic = settings.get("subscribe_topic", f"{self.publish_topic}/control")
        self.get_duration = None

        self.signal_buffer = None
        self.signal_handler = None

    def setup(self, generator: Callable[[float], list]):
        self.signal_buffer = SignalBuffer.precompute(
            self.generation_count,
            lambda i: generator(
                remap(i, 0, self.generation_count - 1, self.generation_min, self.generation_max)
            )
        )
        self.signal_handler = PeriodicSignalHandler(self.signal_buffer)

        return self

    def start(self):
        self.signal_handler.reset_signal()

        # Connect to broker
        client = mqtt.Client()
        client.on_message = self._on_message_callback
        try:
            client.connect(self.broker_host, self.broker_port, keepalive=60)
            client.loop_start()
        except Exception as e:
            print(f"Connection failed: {e}")
            return

        try:
            while True:
                # Signal and current UTC timestamp in ms
                signal = self.signal_handler.get_signal()
                timestamp = int(datetime.now(timezone.utc).timestamp() * 1_000)

                # Publish
                csv_row = f"{timestamp},{signal}|"
                client.publish(self.publish_topic, csv_row, qos=1, retain=False)
                # print(f"Published: {csv_row}")

                # Wait for the configured publish period
                time.sleep(self.publish_period)

        except KeyboardInterrupt:
            pass
    def _on_message_callback(self, client, userdata, message):
        try:
            # Decode payload to string and int value
            payload_str = message.payload.decode("utf-8")
            value = int(payload_str)
            # Calculate targets and queue next signal index
            target_index = remap(value, self.generation_min, self.generation_max, 0, self.generation_count - 1)
            target_duration = self.get_duration(value)
            self.signal_handler.next_index(target_index, target_duration)
                    
        except Exception as e:
            print(f"Error in message callback: {e}")
file = """
name:
  borker_host: 192.168.1.104
  borker_port: 1883
  publish_topic: source/live/patient_monitor/name
  publish_period: 10
  generation_min: 20
  generation_max: 120
  generation_count: 20
ecg:
    publish_topic: source/live/patient_monitor_ecg
    publish_period: 30
    generation_min: 50
    generation_max: 150
    generation_count: 20

"""


config = yaml.safe_load(file)

ecg = """
name:
  borker_host: 192.168.1.104
  borker_port: 1883
  publish_topic: source/live/patient_monitor/name
  publish_period: 10
  generation_min: 20
  generation_max: 120
  generation_count: 20
"""


SignalGenerator(config["name"]).setup(
    lambda x: np.sin(2 * np.pi * np.arange(1000) / 1000).tolist(),
    lambda x: x
).start()

