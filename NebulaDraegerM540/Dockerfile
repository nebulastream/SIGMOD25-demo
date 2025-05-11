FROM python:3.10-slim

WORKDIR /

COPY src /src
COPY requirements.txt /

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python3", "/src/main.py"]