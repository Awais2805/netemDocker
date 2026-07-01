FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        libpcap0.8 tcpdump git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip && pip install --no-cache-dir git+https://github.com/hieulw/cicflowmeter.git

CMD ["sleep", "infinity"]

