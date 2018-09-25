#!/bin/bash

chmod +x /usr/bin/pynetmap-server
chmod +x /usr/bin/pynetmap-server-bin/*
groupadd pynetmap
useradd -d /var/lib/pynetmap/ -G pynetmap -s /usr/bin/pynetmap-server/pynetmap-proxy pynetmap
echo "pynetmap:5WGZ3JG42M6115OP3J5QDMK8I49OM2WX" | chpasswd 
chown pynetmap:pynetmap /var/lib/pynetmap -R
chmod 700 /var/lib/pynetmap -R

echo "# PyNetMAP" >> /etc/ssh/sshd_config
echo "Match User pynetmap" >> /etc/ssh/sshd_config
echo "      ForceCommand /usr/bin/pynetmap-proxy" >> /etc/ssh/sshd_config

systemctl restart ssh
systemctl daemon-reload
systemctl enable pynetmap-server
