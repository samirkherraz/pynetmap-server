#!/bin/bash

chmod +x /usr/bin/pynetmap-server
chmod +x /usr/bin/pynetmap-server-bin/*
groupadd pynetmap
useradd -d /var/lib/pynetmap/ -G pynetmap -s /usr/bin/pynetmap-server/pynetmap-proxy pynetmap

chown pynetmap:pynetmap /var/lib/pynetmap -R
chmod 700 /var/lib/pynetmap -R

systemctl daemon-reload
systemctl enable pynetmap-server
