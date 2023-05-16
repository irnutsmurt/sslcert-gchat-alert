import configparser
import ssl
import datetime
import requests
import socket
import pprint
import OpenSSL
import time
import os

def read_domains(filename="domainlist.conf"):
    if not os.path.exists(filename):
        print(f"Error: {filename} file not found.")
        exit(1)

    with open(filename, "r") as file:
        domains = [line.strip() for line in file.readlines()]

    return domains

def check_ssl_expiry(domain):
    print(f"Checking SSL certificate for {domain}")
    if ':' in domain:
        domain, port = domain.split(':')
        port = int(port)
    else:
        port = 443
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5.0)

    try:
        sock.connect((domain, port))
    except socket.gaierror as e:
        print(f"Error resolving domain {domain}: {e}")
        return None

    context = OpenSSL.SSL.Context(OpenSSL.SSL.TLSv1_2_METHOD)
    conn = OpenSSL.SSL.Connection(context, sock)
    conn.set_tlsext_host_name(domain.encode())
    conn.set_connect_state()

    # Set the socket to blocking mode
    sock.setblocking(1)

    conn.do_handshake()
    ssl_info = conn.get_peer_certificate()
    conn.close()
    expires_on = datetime.datetime.strptime(
        ssl_info.get_notAfter().decode('ascii'), "%Y%m%d%H%M%SZ"
    )
    days_left = (expires_on - datetime.datetime.utcnow()).days
    print(f"SSL certificate for {domain} expires in {days_left} days")
    return days_left

def check_certificate_renewal(domain, original_days_left, sleep_seconds=3600):
    time.sleep(sleep_seconds)
    renewed_days_left = check_ssl_expiry(domain)
    if renewed_days_left > original_days_left:
        print(f"🔄 SSL certificate for {domain} has been renewed! It is now valid for {renewed_days_left} days.")
    else:
        print(f"❗ SSL certificate for {domain} has not been renewed yet. It is still valid for {renewed_days_left} days.")

def read_expiring_certs(filename="expiring_certs.txt"):
    if not os.path.exists(filename):
        with open(filename, "w") as file:
            pass
        return {}

    expiring_certs = {}
    with open(filename, "r") as file:
        for line in file.readlines():
            domain, alerted_date = line.strip().split(' ')
            alerted_date = datetime.datetime.strptime(alerted_date, "%Y-%m-%dT%H:%M:%S.%f")
            expiring_certs[domain] = alerted_date

    return expiring_certs

def write_expiring_certs(expiring_certs, filename="expiring_certs.txt"):
    with open(filename, "w") as file:
        for domain, alerted_date in expiring_certs.items():
            file.write(f"{domain} {alerted_date.isoformat()}\n")

def google_chat_alert(webhook_url, service_name, days_left, alert_days, alert_again, expiring_certs):
    if days_left <= 0:
        if service_name not in expiring_certs or (datetime.datetime.now() - expiring_certs[service_name]).days >= alert_again:
            message = f"❌ SSL certificate for {service_name} has expired! Please Renew Immediately!"
            send_alert(webhook_url, service_name, message)
            expiring_certs[service_name] = datetime.datetime.now()
    elif days_left <= alert_days:
        if service_name not in expiring_certs or (datetime.datetime.now() - expiring_certs[service_name]).days >= alert_again:
            message = f"⚠️ SSL certificate for {service_name} will expire in {days_left} days!"
            send_alert(webhook_url, service_name, message)
            expiring_certs[service_name] = datetime.datetime.now()
    elif service_name in expiring_certs:
        del expiring_certs[service_name]
        message = f"✅ SSL certificate for {service_name} has been renewed! It is now valid for {days_left} days."
        send_alert(webhook_url, service_name, message)
    write_expiring_certs(expiring_certs)

def send_alert(webhook_url, service_name, message):
    print(f"Sending Google Chat alert for {service_name}")
    headers = {'Content-Type': 'application/json'}
    data = {
        "text": message
    }
    response = requests.post(webhook_url, json=data, headers=headers)
    if response.status_code != 200:
        print(f"Failed to send SSL certificate alert: {response.text}")
    else:
        print(f"Sent SSL certificate alert for {service_name}")

def main():
    config = configparser.ConfigParser()
    config.read('config.ini')
    chat_webhook_url = config['chat_webhook']['webhook_url']
    domains = read_domains()
    alert_days = int(config['domains']['alert_days'])
    alert_again = int(config['domains']['alert_again'])
    expiring_certs = read_expiring_certs()

    for domain in domains:
        domain = domain.strip()
        days_left = check_ssl_expiry(domain)

        if days_left <= alert_days:
            if expiring_certs.get(domain) is None or (datetime.datetime.now() - expiring_certs.get(domain)).days >= alert_again:
                google_chat_alert(chat_webhook_url, domain, days_left, alert_days, alert_again, expiring_certs)
                expiring_certs[domain] = datetime.datetime.now()
                write_expiring_certs(expiring_certs)
            else:
                next_alert_in_days = alert_again - (datetime.datetime.now() - expiring_certs.get(domain)).days
                print(f"Domain {domain} has already been alerted on. Next alert in {next_alert_in_days} days.")
        elif domain in expiring_certs:
            # The certificate has been renewed, send an alert
            message = f"✅ SSL certificate for {domain} has been renewed! It is now valid for {days_left} days."
            send_alert(chat_webhook_url, domain, message)
            # Now remove the domain from expiring_certs
            del expiring_certs[domain]
            write_expiring_certs(expiring_certs)

    time.sleep(86400)

if __name__ == '__main__':
    main()
