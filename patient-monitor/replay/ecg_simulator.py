"""
ECG Signal Simulator (MVP)
- Simulates ECG in Normal (70 bpm) and Critical (50 bpm) states.
- Starts in Normal.
- Listens to trigger topic: any message → switch to Critical.
- After critical_timeout (default 15s), auto-switches back to Normal.
- Re-triggerable: multiple cycles allowed.
- Precomputed ECG cycles → zero visual artifacts.
- Configurable via config.yml.
- Uses neurokit2 for realistic ECG generation.
"""

import neurokit2 as nk
import numpy as np
import time
from datetime import datetime, timezone
import paho.mqtt.client as mqtt
import yaml
from pathlib import Path
import logging
from typing import Dict, Any, Optional


# -----------------------------
# CONFIGURATION & LOGGING
# -----------------------------

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default config path
CONFIG_PATH = "config.yml"


def load_config(path: str | Path = CONFIG_PATH) -> Dict[str, Any]:
    """
    Load and validate config from YAML file.
    Returns dict with defaults if missing.
    """
    p = Path(path)
    if not p.is_file():
        logger.warning(f"Config file {path} not found. Using defaults.")
        return {}

    try:
        with p.open() as f:
            config = yaml.safe_load(f) or {}
        return config
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {}


# -----------------------------
# ECG SIGNAL GENERATOR
# -----------------------------

class ECGSignalGenerator:
    """
    Preloads ECG cycles for different heart rates.
    Provides circular indexing to avoid discontinuities.
    """

    def __init__(self, sampling_rate: int = 180, method: str = "daubechies"):
        self.sampling_rate = sampling_rate
        self.method = method
        self.cycles: Dict[str, np.ndarray] = {}

    def generate_cycle(self, heart_rate: int, duration: float = 3.0) -> np.ndarray:
        """
        Generate one full ECG cycle at given heart rate.
        Duration is approx. 1 cycle (e.g., 1/heart_rate * 60).
        """
        # Calculate duration in seconds
        cycle_duration = 60 / heart_rate  # seconds per beat
        # Use longer duration to avoid edge effects
        duration = min(duration, cycle_duration * 1.1)

        # Generate ECG
        ecg = nk.ecg_simulate(
            duration=duration,
            sampling_rate=self.sampling_rate,
            heart_rate=heart_rate,
            method=self.method,
            random_state=42
        )

        # Trim to full cycle (approx. 1 beat)
        # We'll use the first full cycle
        cycle_length = int(self.sampling_rate * cycle_duration)
        if len(ecg) < cycle_length:
            # Pad if needed
            ecg = np.tile(ecg, int(cycle_length / len(ecg)) + 1)
        return ecg[:cycle_length]

    def preload_states(self, config: Dict[str, Any]) -> None:
        """
        Preload ECG cycles for all defined states.
        Expected config:
        ecg:
          states:
            normal:
              heart_rate: 70
              duration: 3.0
            critical:
              heart_rate: 50
              duration: 3.0
        """
        states = config.get("ecg", {}).get("states", {})
        if not states:
            logger.warning("No states defined in config. Using default: normal=70, critical=50.")
            states = {
                "normal": {"heart_rate": 70, "duration": 3.0},
                "critical": {"heart_rate": 50, "duration": 3.0}
            }

        for name, params in states.items():
            heart_rate = params["heart_rate"]
            duration = params.get("duration", 3.0)
            logger.info(f"Preloading ECG cycle for '{name}' (HR={heart_rate} bpm, duration={duration}s)")
            cycle = self.generate_cycle(heart_rate=heart_rate, duration=duration)
            self.cycles[name] = cycle
            logger.debug(f"  → Cycle length: {len(cycle)} samples")

    def get_next_sample(self, state: str, index: int) -> float:
        """
        Get next ECG sample from the cycle for given state.
        Uses circular indexing.
        """
        if state not in self.cycles:
            logger.error(f"Unknown state: {state}. Returning 0.0.")
            return 0.0
        cycle = self.cycles[state]
        return float(cycle[index % len(cycle)])


# -----------------------------
# STATE CONTROLLER
# -----------------------------

class ECGStateController:
    """
    Manages state transitions: Normal → Critical → Normal.
    Tracks timeout and trigger state.
    """

    def __init__(self, critical_timeout: float = 15.0):
        self.critical_timeout = critical_timeout
        self.current_state = "normal"
        self.entry_time: Optional[float] = None
        self.triggered = False  # Prevents multiple triggers during timeout

    def is_in_critical(self) -> bool:
        return self.current_state == "critical"

    def is_timeout_expired(self) -> bool:
        if not self.entry_time:
            return True
        elapsed = time.time() - self.entry_time
        return elapsed >= self.critical_timeout

    def on_trigger(self) -> bool:
        """
        Called when trigger is received.
        Returns True if transition is allowed.
        """
        if self.current_state == "critical":
            logger.info("Trigger received during Critical state. Ignoring (re-trigger not allowed).")
            return False

        if self.triggered:
            logger.info("Trigger already active. Ignoring.")
            return False

        self.current_state = "critical"
        self.entry_time = time.time()
        self.triggered = True
        logger.info("Switched to Critical state. Starting timeout...")
        return True

    def check_and_return_to_normal(self) -> bool:
        """
        Check if timeout expired. If yes, return to Normal.
        Returns True if state changed.
        """
        if self.current_state != "critical":
            return False

        if self.is_timeout_expired():
            self.current_state = "normal"
            self.entry_time = None
            self.triggered = False
            logger.info("Timeout expired. Switched back to Normal state.")
            return True
        return False


# -----------------------------
# MQTT CLIENT MANAGER
# -----------------------------

class MQTTClientManager:
    """
    Handles MQTT connection, publishing, and subscription.
    """

    def __init__(self, broker: str, port: int, topic: str, trigger_topic: str):
        self.broker = broker
        self.port = port
        self.topic = topic
        self.trigger_topic = trigger_topic
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.connected = False

    def connect(self) -> bool:
        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            logger.info(f"Connected to MQTT broker: {self.broker}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False

    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            logger.info("[✓] Connected to MQTT broker")
            self.connected = True
            # Subscribe to trigger topic
            self.client.subscribe(self.trigger_topic)
            logger.info(f"Subscribed to trigger topic: {self.trigger_topic}")
        else:
            logger.error(f"[!] Connection failed (rc={rc})")

    def on_message(self, client, userdata, msg):
        logger.info(f"Trigger received on topic '{msg.topic}': {msg.payload.decode()}")
        # Any message triggers Critical state
        state_controller.on_trigger()

    def publish(self, timestamp: int, value: float) -> None:
        if not self.connected:
            logger.warning("MQTT not connected. Skipping publish.")
            return
        try:
            csv_row = f"{timestamp},{value}|"
            self.client.publish(self.topic, csv_row, qos=1, retain=False)
        except Exception as e:
            logger.error(f"Failed to publish: {e}")

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("MQTT client disconnected.")


# -----------------------------
# MAIN STREAMER
# -----------------------------

class ECGStreamer:
    """
    Main orchestrator: coordinates all components.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ecg_gen = ECGSignalGenerator(sampling_rate=180)
        self.state_controller = ECGStateController(
            critical_timeout=config.get("ecg", {}).get("critical_timeout", 15.0)
        )
        self.mqtt = MQTTClientManager(
            broker=config.get("ecg", {}).get("broker", "localhost"),
            port=config.get("ecg", {}).get("port", 1883),
            topic=config.get("ecg", {}).get("topic", "sink/live/patient_monitor_ecg_value"),
            trigger_topic=config.get("ecg", {}).get("trigger_topic", "trigger/live/patient_monitor_ecg")
        )
        self.publish_period = config.get("ecg", {}).get("period", 30) / 1000.0  # ms → s
        self.current_state = "normal"
        self.index = 0

    def run(self):
        """Main loop."""
        logger.info("Starting ECG streamer...")

        # Load config
        config = self.config.get("ecg", {})
        if not config:
            logger.error("No 'ecg' section in config. Exiting.")
            return

        # Preload ECG cycles
        self.ecg_gen.preload_states(config)

        # Connect to MQTT
        if not self.mqtt.connect():
            logger.error("Failed to connect to MQTT. Exiting.")
            return

        # Start in Normal state
        self.current_state = "normal"
        logger.info("Starting in Normal state.")

        try:
            while True:
                # Check for timeout
                if self.state_controller.check_and_return_to_normal():
                    self.current_state = "normal"
                    self.index = 0  # Reset index

                # Get current state
                state = self.state_controller.current_state

                # Get next ECG sample
                timestamp = int(datetime.now(timezone.utc).timestamp() * 1_000)
                value = self.ecg_gen.get_next_sample(state, self.index)

                # Publish
                self.mqtt.publish(timestamp, value)

                # Update index
                self.index += 1

                # Wait
                time.sleep(self.publish_period)

        except KeyboardInterrupt:
            logger.info("\n[×] Stopping ECG streamer...")
        finally:
            self.mqtt.disconnect()


# -----------------------------
# ENTRY POINT
# -----------------------------

if __name__ == "__main__":
    # Load config
    config = load_config(CONFIG_PATH)

    # Create and run streamer
    streamer = ECGStreamer(config)
    streamer.run()