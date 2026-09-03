# ECG Simulator PoC
## Execute
The ECG PoC is prepared with a `docker-compose` that includes an MQTT broker to test it.
```bash
# Build the containers and start them.
docker-compose -f docker-compose-simulator.yml up --build

# Submit the trigger
docker exec -it ecg-simulator mosquitto_pub -h localhost -t "trigger/live/patient_monitor_ecg" -m "critical"

# Visualize in CLI the MQTT Topic
docker exec -it ecg-simulator mosquitto_sub -h localhost -t "sink/live/patient_monitor_ecg_value"

```
