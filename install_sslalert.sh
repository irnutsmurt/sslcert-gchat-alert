#!/bin/bash

# Create the 'sslalert' user with no login
sudo useradd -r -s /bin/false sslalert

# Change the ownership and permissions of the necessary files
sudo chown sslalert:root config.ini domainlist.conf expiring_certs.txt sslcert_check.py
sudo chmod 660 config.ini domainlist.conf expiring_certs.txt sslcert_check.py

# Set the working directory as the directory containing this script
working_dir=$(dirname "$(realpath "$0")")

# Create a systemd service file
sslalert_service="[Unit]
Description=SSL Alert Service

[Service]
Type=simple
User=sslalert
Group=root
WorkingDirectory=$working_dir
ExecStart=/usr/bin/python3 $working_dir/sslcert_check.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target"

# Create the systemd service file and enable the service
echo "$sslalert_service" | sudo tee /etc/systemd/system/sslalert.service
sudo systemctl daemon-reload
sudo systemctl enable sslalert.service
sudo systemctl start sslalert.service

echo "SSL Alert Service has been created, enabled, and started."
