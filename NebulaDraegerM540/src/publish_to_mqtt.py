import json
import logging

import paho.mqtt.client as mqtt

clients = {}

def publish_mqtt(draeger_label, timestamp_iso, param_value, config):

    broker_key = f"{config['mqtt_broker']}:{config['mqtt_port']}"

    # reuse existing client or create a new one
    if broker_key not in clients:
        try:
            client = mqtt.Client()
            client.connect(config['mqtt_broker'], config['mqtt_port'],  config['mqtt_keepalive'])
            clients[broker_key] = client
            logging.info(f"[MQTT] Connected to MQTT")
        except Exception as e:
            logging.warning(f"[MQTT] Failed to connect to MQTT broker {broker_key}: {e}")
            return

    client = clients[broker_key]

    if config["mqtt_format"] == "json":
        #value = value_type(param_value)  # casting
        payload = json.dumps({"timestamp": timestamp_iso, "value": param_value})
        topic = config['mqtt_topic'] + "/" + draeger_label
        client.publish(topic, payload)
        logging.info(f"[MQTT] Sent to {broker_key} (topic: {topic}): {payload} ")
    elif config["mqtt_format"] == "csv":
        payload = str(str(timestamp_iso) + "," + str(param_value))
        topic = config['mqtt_topic']+"/"+draeger_label
        client.publish(topic, payload)
        # add_to_buffer(payload)
        logging.info(f"[MQTT] Sent to {broker_key} (topic: {topic}): {payload} ")
    else:
        logging.warning("[MQTT] Unknown data format")