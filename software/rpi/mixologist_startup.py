#!/usr/bin/python3

#
# Created by mstark on February 10, 2018
#
# Copyright 2018 Michael Stark. All Rights Reserved.
#


import subprocess
import traceback
import os, sys

WPA_FILE_PATH = "/etc/wpa_supplicant/wpa_supplicant.conf"

# network={
# ssid="YOUR_NETWORK_NAME"
# psk="YOUR_NETWORK_PASSWORD"
# proto=RSN
# key_mgmt=WPA-PSK
# pairwise=CCMP
# auth_alg=OPEN
# }

INTOUCH_GUEST_NETWORK = {
    "ssid": "Intouch Guest",
    "psk": "Int14GuestNet",
    "id_str": "IntouchGuestWifi"
}


JACOB_NETWORK = {
    "ssid": "Jacob-iPhone-X",
    "psk": "jacoblovesgabi",
    "id_str": "JacobNetwork"
}

BAPTISTELLA_NETWORK = {
    "ssid": "baptistella",
    "psk": "gabiswake",
    "key_mgmt": "WPA-PSK", # no quotes
    "id_str": "BaptistellaNetwork"
}


def write_network(network):
    contents = []
    with open(WPA_FILE_PATH, 'r+') as file:
        contents = file.readlines()
        file.close()

    contents.append("\n")
    contents.append("network={\n")
    for prop in network:
        contents.append("   {prop}=\"{val}\"\n".format(prop=prop, val=network[prop]))
    contents.append("\n")
    contents.append("}")
    contents.append("\n")

    with open(WPA_FILE_PATH, 'w+') as file:
        file.seek(0)
        file.writelines(contents)
        file.close()


def is_connected():
    """Check wlan0 has an IP address."""
    output = subprocess.check_output(['ifconfig', 'wlan0']).decode('utf-8')

    return 'inet ' in output

def check_network_config():
    """Check wpa_supplicant.conf has at least one network configured."""
    config = subprocess.check_output(['sudo', 'cat', WPA_CONF_PATH]).decode('utf-8')
    
    if not 'IntouchGuestWifi' in config:
        write_network(INTOUCH_GUEST_NETWORK)
    if not 'JacobNetwork' in config:
        write_network(JACOB_NETWORK)
    if not 'BaptistellaNetwork' in config:
        write_network(BAPTISTELLA_NETWORK)


def connect():
    os.system("sudo wpa_cli -i wlan0 reconfigure")

def startup_wifi():
    os.system("sudo ifconfig wlan0 up")


def find_ip():
    os.system("ifconfig wlan0 > /tmp/ipaddr.txt")
    with open('/tmp/ipaddr.txt', 'r+') as file:
        contents = file.readlines()
        print(contents)
        for item in contents:
            if item.strip('\t').startswith('inet '):
                return item.strip().split(' ')[1]
    return ""
    

def send_ip():
    os.system("curl -X POST -H \"Content-Type: application/json\" -d '{\"value1\":\"{ipaddr}\",\"value2\":\"Wifi is connected.\"' https://maker.ifttt.com/trigger/SendMixologistIPAddress/with/key/pEei3L_T0sbAiAXkrMMEUUGyKshTnolB_qcU0mp5DS9".format(ipaddr=find_ip()))


def startup_mixologist():
    os.system("cd /home/pi/")
    os.system("amixer set PCM 93%")
    # source /home/pi/env/bin/activate
    # python -m assistant-sdk-python.google-assistant-sdk.googlesamples.rpi
    subprocess.run(['source', '/home/pi/env/bin/activate', '&&', 'python','-m', 'assistant-sdk-python.google-assistant-sdk.googlesamples.rpi'])
    


def main():
    if not is_connected():
        startup_wifi()
        check_network_config()
        connect()
        send_ip()
    startup_mixologist()


if __name__ == "__main__":
    try:
        if 'test' in sys.argv:
            write_network(INTOUCH_GUEST_NETWORK)
        else:
            main()
    except:  # pylint: disable=bare-except
        traceback.print_exc()