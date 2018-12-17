#!/bin/bash

pip3 install proxmoxer zabbix_api requests paramiko  

chmod +x /usr/bin/pynetmap-server
chmod +x /usr/bin/pynetmap-server-bin/*
echo " -- [ CLEANUP ] -- "

userdel pynetmap 

grep -v "# PyNetMAP" /etc/ssh/sshd_config > /etc/ssh/sshd_config.back
mv  /etc/ssh/sshd_config.back /etc/ssh/sshd_config
echo " -- [ SETUP ] -- "
groupadd pynetmap
useradd -d /var/lib/pynetmap/ -g pynetmap pynetmap
echo "pynetmap:5WGZ3JG42M6115OP3J5QDMK8I49OM2WX" | chpasswd 
chown pynetmap:pynetmap /var/lib/pynetmap -R
chmod 700 /var/lib/pynetmap -R
echo "# PyNetMAP" >> /etc/ssh/sshd_config
echo "Match User pynetmap # PyNetMAP" >> /etc/ssh/sshd_config
echo "      ForceCommand /usr/bin/pynetmap-proxy # PyNetMAP" >> /etc/ssh/sshd_config

systemctl restart ssh
systemctl daemon-reload
systemctl enable pynetmap-server
