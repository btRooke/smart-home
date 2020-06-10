import network
import time
from utilities import *

"""
Delay before function returns if connection to wifi network was sucessful
as it takes a while to connect if it was sucessful.
"""

CONNECTION_DELAY = 10

"""
All of these functions are designed to be called by a device communicating via
the serial prort to configure the device.
"""

def ping(): # Lets a serial program know it's here
    print ("Okay")

def connect_to_network(ssid, password):
    sta_if = network.WLAN(network.STA_IF)
    sta_if.connect(ssid, password)

    time.sleep(CONNECTION_DELAY)

    if sta_if.isconnected():
        print("True")

    else:
        print("False")

def get_ip_and_auth_key():
    sta_if = network.WLAN(network.STA_IF)
    ip = sta_if.ifconfig()[0]

    auth_key = read_file(AUTH_KEY_FILE_NAME)

    print(ip + ":" + auth_key)
