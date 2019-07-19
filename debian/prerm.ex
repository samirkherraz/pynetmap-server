#!/bin/bash

pyclean /usr/bin/pynetmap-server-bin/


sed -i '/# PyNetMAP/d' /etc/ssh/sshd_config
