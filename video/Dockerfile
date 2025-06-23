FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY replay.py test.csv ./

RUN pip install --no-cache-dir paho-mqtt

CMD ["python", "replay.py"]
