#!/bin/sh
set -e

# Varied-size pages -> benign HTTP responses span a range of packet sizes
# (run B: breaks the single-page packet-length shortcut from run A).
mkdir -p /var/www/html/pages
for kb in 1 4 16 64 256; do
    {
        echo "<html><body><h1>page ${kb}k</h1><pre>"
        head -c "$((kb*1024))" /dev/urandom | base64
        echo "</pre></body></html>"
    } > "/var/www/html/pages/p${kb}k.html"
done

/usr/sbin/sshd
exec nginx -g "daemon off;"
