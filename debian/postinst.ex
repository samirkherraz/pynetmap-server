#!/bin/bash

chmod +x /usr/bin/pynetmap-server
chmod +x /usr/bin/pynetmap-server-bin/*

systemctl daemon-reload
systemctl enable pynetmap-server
