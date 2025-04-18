FROM alpine:3.21
RUN apk update && apk add \
    socat \
    hexdump \
    ripgrep
COPY ./unpack_u8.sh /bin/unpack_u8.sh
ENTRYPOINT ["/bin/unpack_u8.sh"]
