import random
import pymysql
import string
from flask import Response
import json
import re
import datetime
import socket

DATABASE_DETAILS = {
    "host":"localhost",
    "user":"controllerUser",
    "passwd":"123",
    "db":"controllerDB"}

ERROR_MESSAGE_FILE_NAME = "error_messages.json"
VERBOSE = True

# Classes


class DBConnection:

    """
    Class to be used in conjunction with a 'with' statement as to
    ensure correct usage; connection is closed and opened correctly.
    """

    def call(self, command):
        cursor = self._db.cursor()
        cursor.execute(command)
        to_return = cursor.fetchall()
        cursor.close()

        return to_return

    def last_insert_id(self):
        return self._db.insert_id()

    def __enter__(self, details=DATABASE_DETAILS):
        self._db = db = pymysql.connect(**DATABASE_DETAILS)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # Passed automatically by python.
        self._db.commit()
        self._db.close()


class JSONAPIResponse:
    def __init__(self):
        self._content = {}
        self.set_status(1)

    def set_status(self, code, text=""):
        if not text:
            text = get_error_message(code)

        self._content["status"] = {"code": code, "text": text}

    def add_content(self, content, content_id):
        self._content[content_id] = content

    def build(self):
        response = Response(json.dumps(self._content))
        response.headers["Access-Control-Allow-Origin"] = '*'     # Allows API to be called from any origin.
        response.headers["Content-type"] = "application/json"   # Tells recieving machine that it's getting json.

        return response

class DeviceConnection:
    def __init__(self, host, auth_key, timeout=3.5):
        self._host = host
        self._auth_key = auth_key

        self._sk = socket.socket()
        self._sk.settimeout(timeout)

        """
        The line below will intentionally throw an error if it can't connect
        to a device, this will be dealt with in controller.py.
        """

        self._sk.connect(host)

    def close(self):
        self._sk.close()

    def call_command(self, command):
        to_send = self._auth_key + "," + command

        if VERBOSE:
            print("Sending Command:")
            print(to_send)

        try:
            self._sk.send(to_send.encode())
            response = self._sk.recv(1024)

        except (socket.timeout, ConnectionResetError):
            return False

        response = response.decode()

        return json.loads(response)

# Functions

def print_posted_values(flask_response_object):
    print("Recieved post values: " + "".join(["\n" + str(key) + ": " + str(flask_response_object.json[key]) for key in flask_response_object.json.keys()]))


def generate_session_key(length=32):
    return "".join([random.choice(string.ascii_letters + string.digits) for i in range(length)])

def is_session_key_valid(key): # not to be used to check if a session key is expired

    KEY_REGEX = "^[A-z0-9]{32}$"

    if not re.match(KEY_REGEX, key):
        return False

    with DBConnection() as conn:
        query = "SELECT sessionKey FROM session WHERE sessionKey='{}';"
        query = query.format(key)
        records = conn.call(query)

    if not records:
        return False
    else:
        return True

def get_error_message(code):
    with open(ERROR_MESSAGE_FILE_NAME, "r") as f:
        data = f.read()

    codes = json.loads(data)

    if str(code) in codes.keys():
        return codes[str(code)]
    else:
        return ""

def update_session_last_request_time(session_key):
    with DBConnection() as conn:
        current_date_and_time = datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        query = "UPDATE session lastRequestTime='{}' WHERE sessionKey = '{}';".format(current_date_and_time, session_key)


def session_has_permission_for_device(session_key, device_id):
    with DBConnection() as conn:
        query = "SELECT userID FROM session WHERE sessionKey = '{}'"
        user_id = conn.call(query.format(session_key))[0][0]

        query = "SELECT ownerID FROM device WHERE deviceID = {}"
        owner_id = conn.call(query.format(device_id))[0][0]

    if user_id == owner_id:
        if VERBOSE:
            print("Permission granted as caller is owner.")
        return True

    with DBConnection() as conn:
        query = "SELECT permissionType.name FROM permission INNER JOIN permissionType ON permission.permissionTypeID = permissionType.typeID WHERE permission.deviceID = {}"
        permission_type = conn.call(query.format(device_id))[0][0]

    if permission_type == "disallow_all":
        if VERBOSE:
            print("Permission disallowed as disallow_all is active.")
        return False

    elif permission_type == "allow_all":
        if VERBOSE:
            print("Permission granted as allow_all is active.")

        return True

    with DBConnection() as conn:
        query = "SELECT userInPermission.userID FROM userInPermission INNER JOIN permission ON userInPermission.permissionID = permission.permissionID WHERE permission.deviceID = {}"
        users_in_permission = conn.call(query.format(device_id))

    users_in_permission = [record[0] for record in users_in_permission]

    if user_id in users_in_permission:
        if permission_type == "blacklist":
            if VERBOSE:
                print("Permission disallowed as caller is in blacklist.")

            return False

        elif permission_type == "whitelist":
            if VERBOSE:
                print("Permission allowed as caller is in whitelist.")

            return True
    else:
        if permission_type == "blacklist":
            if VERBOSE:
                print("Permission allowed as caller is not in blacklist.")
            return True

        elif permission_type == "whitelist":
            if VERBOSE:
                print("Permission disallowed as caller is not in whitelist.")
            return False
