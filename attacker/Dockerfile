FROM debian:12-slim 

RUN apt-get update && apt-get install -y --no-install-recommends \
    nmap hping3 hydra python3-pip iputils-ping \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages slowloris

CMD ["sleep", "infinity"]

