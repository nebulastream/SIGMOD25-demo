import logging
import queue
import threading
from datetime import datetime

from publish_to_mqtt import publish_mqtt
from publish_to_tcp import publish_tcp

# message queues for each protocol per Draeger label / signal
message_queues_mqtt: dict[str, queue.Queue] = {}
message_queues_tcp: dict[str, queue.Queue] = {}

# worker threads for each protocol per Draeger label / signal
worker_threads_mqtt: dict[str, threading.Thread] = {}
worker_threads_tcp: dict[str, threading.Thread] = {}

# param_code to topics. Choose according to "Code" / "Dräger Label"-column in RS-232 export protocol. You can pick a datatype for casting that fits; default is str. Useful when transmitting json via mqtt.
param_map: dict[int, tuple[str, type]] | dict[int, str] = {
    0x01: ("HR", int),
    0x31: ("GP1a", int), #GP1 is blood pressure (General Purpose BP Channel 1)
    0x32: ("GP1b", int),
    0x33: ("GP1c", int),
    0x64: ("SPO2", int),
    0x65: ("PLS", int),
    0x6F: ("TEMP", float),
}

def make_message(param_code: int, param_value: str, signals_config) -> None:
    timestamp_iso = datetime.now().timestamp()

    if param_code not in param_map:
        return

    draeger_label, value_type = param_map[param_code]

    try:
        param_value = value_type(param_value)  # ***^^e is sent when sensor is taken off so casting will raise exception
    except Exception as e:
        logging.warning(f"Failed to cast. Was the sensor taken off? {e}")
        return

    # initialize queues and threads per Draeger label if not exists
    if draeger_label not in message_queues_mqtt:
        message_queues_mqtt[draeger_label] = queue.Queue()
        worker_threads_mqtt[draeger_label] = threading.Thread(
            target=worker_thread_mqtt, args=(draeger_label,), daemon=True
        )
        worker_threads_mqtt[draeger_label].start()

    if draeger_label not in message_queues_tcp:
        message_queues_tcp[draeger_label] = queue.Queue()
        worker_threads_tcp[draeger_label] = threading.Thread(
            target=worker_thread_tcp, args=(draeger_label,), daemon=True
        )
        worker_threads_tcp[draeger_label].start()

    # add message to the corresponding queue, one for each transfer protocol
    for signal in signals_config:

        if signal['signal'] != draeger_label:
            continue

        if signal['transfer_protocol'].lower() == "mqtt":
            message_queues_mqtt[draeger_label].put((timestamp_iso, param_value, signal))
        elif signal['transfer_protocol'].lower() == "tcp":
            message_queues_tcp[draeger_label].put((timestamp_iso, param_value, signal))

def worker_thread_mqtt(draeger_label: str):
    """worker to process MQTT messages"""
    while True:
        timestamp_iso, param_value, signal = message_queues_mqtt[draeger_label].get()
        publish_mqtt(draeger_label, timestamp_iso, param_value, signal)
        message_queues_mqtt[draeger_label].task_done()

def worker_thread_tcp(draeger_label: str):
    """worker to process TCP messages"""
    while True:
        timestamp_iso, param_value, signal = message_queues_tcp[draeger_label].get()
        publish_tcp(draeger_label, int(timestamp_iso * 1000), param_value, signal)
        message_queues_tcp[draeger_label].task_done()
