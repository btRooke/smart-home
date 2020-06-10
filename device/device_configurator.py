import serial
import time

SERIAL_CONFIGURATION = {
    "baudrate": 115200,
    "bytesize": serial.EIGHTBITS,
    "stopbits": serial.STOPBITS_ONE,
    "timeout": 0.5
}

CARRIGE_RETURN = "\r\n" # This needs to be sent after each command.

CONNECTION_WAIT_TIME = 12

def get_response(recieved, line_breaks=1):
        """
        Command is echoed back, then the return value on next line
        then the prompt on the next and so splitting on the carrige return
        and selecting the secodnd value gives us what we want.
        """

        if CARRIGE_RETURN in recieved:
            recieved = recieved.split(CARRIGE_RETURN)[line_breaks]

            return recieved

        else:
            return ""


def get_iot_device_ports():
    ports = []

    """
    Windows offers up ports COM[1-256] as serial communication ports so
    what we're doing here is trying to connect to each one, and if we do,
    we are sending the ping() command which is programmed into my devices
    which simply returns "Okay", if it does so, we know that it is a device we
    want to program.
    """

    for i in range(1, 257):
        potenial_port = "COM" + str(i)

        try:
            with serial.Serial(**SERIAL_CONFIGURATION, port=potenial_port) as conn:
                conn.write("\x03".encode()) # effectively a CTRL + C break the server listening loop so we can talk to the device
                conn.write(("ping()" + CARRIGE_RETURN).encode())

                recieved = conn.read(256).decode()

        except serial.SerialException:
            continue

        recieved = get_response(recieved, 2)

        if "Okay" in recieved:
            ports.append(potenial_port)

    return ports

def connect_to_network(ssid, password, port):
    with serial.Serial(**SERIAL_CONFIGURATION, port=port) as conn:
        conn.write(("connect_to_network('{}', '{}')".format(ssid, password) + CARRIGE_RETURN).encode())

        time.sleep(CONNECTION_WAIT_TIME)

        recieved = conn.read(256).decode()

    recieved = get_response(recieved)

    if "True" in recieved:
        return True
    elif "False" in recieved:
        return False


def get_ip_and_auth_key(port):
    with serial.Serial(**SERIAL_CONFIGURATION, port=port) as conn:
        conn.write(("get_ip_and_auth_key()" + CARRIGE_RETURN).encode())

        recieved = conn.read(256).decode()

    recieved = get_response(recieved)

    return recieved.split(":")
