#! /usr/bin/bash

set -e

function stop_query() {
    nes-nebuli stop -s nes:8080 $QUERY_ID || echo "Could not stop query $QUERY_ID"
    echo "Stopped"
}

function check_status() {
    if /bin/grpc_health_probe -addr nes:8080; then
        STATUS=$(nes-nebuli status -s nes:8080 $QUERY_ID)
        if [ "$STATUS" == "Running" ]; then 
            return 0       
        elif [ "$STATUS" == "Registered" ]; then
            echo "Registered"
            return 0
        else 
            echo $STATUS
            return 1
        fi
    else
        return 1
    fi
}


QUERY_ID=$(nes-nebuli register -x -s nes:8080 -i $@)
if [ $? -ne 0 ]; then
    echo "Could not start query: $QUERY_ID"
    exit 1
fi
trap stop_query EXIT
echo "Started"

while check_status; do
    sleep 10
done

echo "Status: $(nes-nebuli status -s nes:8080 $QUERY_ID)"