import os
from utilities import *
from configuration import *
import socket
import json
from thermometer import Thermometer

log("File imports sucessful!")

VERBOSE = True

HOST = "0.0.0.0"
DEVICE_PORT = 24601
ADC_PIN = 0

generate_auth_key_if_not_exists()

"""
Unfortunately micropython on the ESP8266 does not support threading at this point
and so only 1 request can be processed at once, however this should be fine as
request collisions should not occur very often.
"""

thermometer = Thermometer(ADC_PIN)

"""
log() logs the string to a text file ("log.txt") which we can have a look at
incase anything goes wrong or we need to see what requests have been occuring
on the device.
"""

log("Thermometer object instantiated!")

# Connection Manager

sk = socket.socket()
sk.bind((HOST, DEVICE_PORT))
sk.listen(1)

while True:
    log("Listening...")
    conn, addr = sk.accept()

    log("Request from " + addr[0])

    data = conn.recv(2048).decode()

    log("They sent " + data)

    command = data.split(",")

    if len(command) != 2:
        conn.send(json.dumps({"code": 2}).encode())
        log("Incorrectly formatted request")
        conn.close()
        continue

    if command[1] not in thermometer.device_commands.keys():
        conn.send(json.dumps({"code": 3}).encode())
        log("The command was not valid for this device")
        conn.close()
        continue

    if not auth_key_is_valid(command[0]):
        conn.send(json.dumps({"code": 1}).encode())
        log("Their auth key wasn't valid")
        conn.close()
        continue

    """
    Bad practise not to specify an error type, however we don't care what
    it is, we just want to the device to let the controller know. Therefore
    it is appropriate in this case.
    """

    log("They called " + command[1])

    try:
        to_send = thermometer.device_commands[command[1]]()
        log("Command calling successful!")
    except Exception as e:
        log("Problem executing command occurred...")
        to_send = json.dumps({"code": 4, "error":e})

    log("We will send back " + to_send)

    to_send = to_send.encode()
    conn.send(to_send)
    conn.close()
