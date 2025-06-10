# ---- Base image ----
FROM python:3.11-slim

# ---- System setup ----
# Grab basic build tools only if/when wheels are missing.
# The extra packages add ~60 MB, so we install them first, then prune.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential       \
        gcc g++              \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY ecg.py ppg.py abp.py config.yml ./

# Rely on manylinux wheels for SciPy/numpy/etc.
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir \
        neurokit2 \
        medical_waveforms \
        paho-mqtt \
        PyYAML   \
        PyWavelets \
 && python -m pip cache purge   # keep the image tiny

# ---- Runtime ----
CMD [ "sh", "-c", "python ecg.py & python ppg.py & python abp.py" ]
