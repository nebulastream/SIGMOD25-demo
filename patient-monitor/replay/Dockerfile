# ---- Base image ----
FROM python:3.11-slim

# ---- System setup ----
# Grab basic build tools only if/when wheels are missing.
# The extra packages add ~60 MB, so we install them first, then prune.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential       \
        gfortran              \
        libatlas-base-dev     \
    && rm -rf /var/lib/apt/lists/*

# ---- Python deps ----
WORKDIR /app
COPY ecg.py .
COPY config.yml .

# Rely on manylinux wheels for SciPy/numpy/etc. Build tools above are insurance.
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir \
        neurokit2 \
        paho-mqtt \
        PyYAML   \
        PyWavelets \
 && python -m pip cache purge   # keep the image tiny

# ---- Runtime ----
# (If you later move to a non-root user, add USER here.)
CMD ["python", "ecg.py"]
