FROM alpine:3.21
RUN apk update
RUN apk add socat
RUN apk add hexdump
COPY ./unpack_u8.sh /bin/unpack_u8.sh
ENTRYPOINT ["/bin/unpack_u8.sh"]
