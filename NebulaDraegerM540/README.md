This README explains how to set up the jumphost for the Draeger Patient Monitor.
The end goal is to have the signals "PLS" and "SPO2" published to mqtt at port 1883. The topics are "patientMonitor/SPO2" / "patientMonitor/PLS"

## Build the correct nebuli image
As of now (May '25), the public nebulastream/nebuli:lastest image does not support MQTT, so we need to build the nebulastream/neubli image locally from this branch:

https://github.com/nebulastream/nebulastream-SIGMOD-Demo/tree/main

You can do so with the same instructions as here (until but not including "Modifying dependencies"):

https://github.com/nebulastream/nebulastream-public/blob/main/docs/technical/development.md

That should give you a binary at _build-docker/nes-nebuli/nes-nebuli_.

Next, set up a Dockerfile at _docker/nebuli-runtime/Dockerfile_ like this:

```
FROM ubuntu:22.04
COPY nes-nebuli /usr/local/bin/nes-nebuli
RUN chmod +x /usr/local/bin/nes-nebuli
ENTRYPOINT ["/usr/local/bin/nes-nebuli"]
```

and build the image:

    docker build -t nebulastream/nebuli:local docker/nebuli-runtime

Check that the image nebulastream/nebuli:local exists:

    docker images

## Build the script image
Now we can proceed with the actual script.
Build the script image (from _SIGMOD25-demo/NebulaDraegerM540_):

    sudo docker build -t m540-script .

## Start the setup
Now, from the _SIGMOD25-demo/NebulaDraegerM540/docker_, just run

    docker-compose up

and you should see something like

    INFO - [MQTT] Sent to mosquitto:1883 (topic: patientMonitor/SPO2): {"timestamp": 1746983826.538433, "value": 100}

## Troubleshooting
You check if topics are being published within the docker network with

    docker exec -it docker-worker-1 sh -c "apt update && apt install -y mosquitto-clients && mosquitto_sub -h mosquitto -p 1883 -t '#'"

or from the jumphost

    mosquitto_sub -h localhost -p 1883 -t "#"