This README explains how to set up the jumphost for the Draeger Patient Monitor.
The end goal is to have the signals "PLS" and "SPO2" published to mqtt at port 1883. The topics are "patientMonitor/SPO2" / "patientMonitor/PLS"

## Build the script image
Build the script image (from _SIGMOD25-demo/NebulaDraegerM540_):

    sudo docker build -t m540-script .

## Start the setup
You need to pass the serial port that the patient monitor is connected to as en envar to the docker compose. Otherwise, it will fall back to /dev/USB0.
It should appear under, depending on your OS.

    ls /dev/tty*

Now, from _SIGMOD25-demo/NebulaDraegerM540/docker_, with the correct USB_DEV=<_correct port_> envar, just run

    USB_DEV=/dev/ttyUSB0 docker-compose up

and you should see something like

    INFO - [MQTT] Sent to mosquitto:1883 (topic: patientMonitor/SPO2): {"timestamp": 1746983826.538433, "value": 100}

## Troubleshooting
You check if topics are being published within the docker network with

    docker exec -it docker-worker-1 sh -c "apt update && apt install -y mosquitto-clients && mosquitto_sub -h mosquitto -p 1883 -t '#'"

or from the jumphost

    mosquitto_sub -h localhost -p 1883 -t "#"