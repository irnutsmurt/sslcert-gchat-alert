# SSL Certificate Expiration Alert

This script checks the expiration dates of SSL certificates for a list of domains and sends alerts to Google Chat using a webhook. The script can be configured to send alerts only when a certificate is about to expire or has expired, and can send repeated alerts based on the configuration.

## Prerequisites

- Python 3.x
- `requests` and `pyOpenSSL` Python packages

You can install the required packages using the following command:

pip install requests pyOpenSSL


## Configuration

1. Update the `config.ini` file with your Google Chat webhook URL and the desired number of days before expiration to trigger an alert:

[domains]
alert_days = 30
alert_again = 5

[chat_webhook]
webhook_url = YOUR_WEBHOOK_URL


2. Create or update the `domainlist.conf` file with a list of domains to check, one per line. If you want to specify a custom port for a domain, add a colon followed by the port number:

exampledomain1.com
exampledomain2.com
exampledomain3.com:3463
exampledomain4.com


## Running the Script

To run the script, simply execute the following command:


By default, the script will loop every 24 hours and check the SSL certificates for the specified domains.

## Setting Up the Service Account and Systemd Service (Optional)

If you want to set up a dedicated service account to run the script and use a systemd service for automatic execution, follow these steps:

1. Save the `install_sslalert.sh` script in the same directory as the `sslcert_check.py` script and the configuration files.

2. Make the `install_sslalert.sh` script executable:

sudo ./install_sslalert.sh


This script will create the 'sslalert' user, set up the necessary permissions, and create a systemd service file. The service will be enabled and started automatically.
