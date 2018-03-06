#!/usr/bin/python3

#
# Created by mstark on February 10, 2018
#
# Copyright 2018 Michael Stark. All Rights Reserved.
#


import subprocess
import traceback
import os, sys, time

WPA_FILE_PATH = "/etc/wpa_supplicant/wpa_supplicant.conf"

from common_settings import wifi_config



def write_network(network):
    contents = []
    with open(WPA_FILE_PATH, 'r+') as file:
        contents = file.readlines()
        file.close()

    contents.append("\n")
    contents.append("network={\n")
    for prop in network:
        # if for adding quotes around value
        if prop in ('ssid', 'psk', 'id_str'):
            contents.append("   {prop}=\"{val}\"\n".format(prop=prop, val=network[prop]))
        else:
            contents.append("   {prop}={val}\n".format(prop=prop, val=network[prop]))
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
    config = subprocess.check_output(['sudo', 'cat', WPA_FILE_PATH]).decode('utf-8')

    for item in wifi_config:
        if 'id_str' in item and not item['id_str'] in config:
            write_network(item)
            

def connect():
    os.system("sudo wpa_cli -i wlan0 reconfigure")

def startup_wifi():
    os.system("sudo ifconfig wlan0 up")


def find_ip():
    os.system("ifconfig wlan0 > /tmp/ipaddr.txt")
    with open('/tmp/ipaddr.txt', 'r+') as file:
        contents = file.readlines()
        # print(contents)
        for item in contents:
            if item.strip().startswith('inet '):
                ip = item.strip().split(' ')[1]
                if ip.startswith('addr'):
                    return ip.split(':')[1]
                return ip
            
    return ""
    

def send_ip():
    """ Send IP via web """
    ip = find_ip()
    print("IP Address: {}".format(ip))
    if len(ip) < 1:
        return
    # add your own endpoint to call
    

def adjust_volume():
    os.system("amixer set PCM 93%")

def startup_mixologist():
    os.system("cd /home/pi/")
    # source /home/pi/env/bin/activate
    # python -m assistant-sdk-python.google-assistant-sdk.googlesamples.rpi
    subprocess.run(['source', '/home/pi/env/bin/activate', '&&', 'python','-m', 'assistant-sdk-python.google-assistant-sdk.googlesamples.rpi'])
    


def main():
    if not is_connected():
        startup_wifi()
        check_network_config()
        connect()
        # wait for network connection
        for i in range(100):
            if is_connected():
                send_ip()
                adjust_volume()
                startup_mixologist()
                return
            else:
                time.sleep(1) # sleep for one second
    else:
        startup_mixologist()


if __name__ == "__main__":
    try:
        if 'wifi' in sys.argv:
            startup_wifi()
            check_network_config()
            connect()
        elif 'ip' in sys.argv:
            print("IP Address: {}".format(find_ip()))
        elif 'sound' in sys.argv:
            print("Adjusting volume")
            adjust_volume()
        else:
            main()
    except:  # pylint: disable=bare-except
        traceback.print_exc()
