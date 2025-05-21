FROM ubuntu:24.04

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      pulseaudio-utils \
      socat \
    && rm -rf /var/lib/apt/lists/*

# create a user with args from Compose
ARG HOST_UID
ARG HOST_GID

# only create the group/user if they don't already exist
RUN set -eux; \
    if ! getent group "${HOST_GID}" >/dev/null; then \
      groupadd -g "${HOST_GID}" hostgroup; \
    fi; \
    if ! id -u "${HOST_UID}" >/dev/null 2>&1; then \
      useradd -m -u "${HOST_UID}" -g "${HOST_GID}" hostuser; \
    fi

USER hostuser
WORKDIR /home/hostuser

CMD ["bash"]
