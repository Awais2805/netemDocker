FROM debian:12-slim 
RUN apt-get update && apt-get install -y --no-install-recommends \
        nginx openssh-server iputils-ping \
    && rm -rd /var/lib/apt/lists/* \
    && mkdir -p /run/sshd 

RUN useradd -m -s /bin/bash victimuser \
    && echo 'victimuser:password123' | chpasswd \
    && sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config \
    && sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config 

EXPOSE 22 80 
COPY start.sh /start.sh
RUN chmod +x /start.sh
CMD ["/start.sh"]

