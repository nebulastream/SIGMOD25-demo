#!/bin/sh

echo "SOURCE_HOST: ${SOURCE_HOST:=localhost}"
echo "SOURCE_PORT: ${SOURCE_PORT:=22345}"
echo "SINK_PORT: ${SINK_PORT:=22346}"

socat -u TCP4:$SOURCE_HOST:$SOURCE_PORT STDOUT \
	| hexdump -v -e '/1 "%03u\n"' \
	| rg --color never "^[0-9]{3}$" \
	| socat -u STDIO TCP-LISTEN:$SINK_PORT,fork

