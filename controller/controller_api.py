from flask import Flask, request
from flask_cors import CORS, cross_origin
import datetime
import re

from utilities import *
import password_hashing as pw

VERBOSE = True
DEVICE_PORT = 24601

app = Flask(__name__)
CORS(app) # Needed to ensure API can be called from anywhere.

@app.route("/create_user", methods=["POST"])
def create_user():
    if VERBOSE:
        print_posted_values(request)

    # Dict for info about what parameters are meant to be supplied to this function (apart from session_key)

    PARAMETERS = {
        "new_username": {
            "RegEx":"^[\w\d]+$",
            "required": True},
        "new_password": {
            "RegEx": "^(?=.*[^\w\d]+.*)(?=.*[A-z]+.*)(?=.*[\d]+.*).{8,}$",
            "required": True},
        "email": {
            "RegEx": "^[^\s]+@[^\s]+\.[^\s]+$",
            "required": False}
        }

    # First checks which parameters the user has supplied with intersection of 2 sets.

    parameters_included = set(PARAMETERS.keys()) & set(request.json.keys())

    # Next checks if the required parameters are in parameters_include with difference of sets, gives items in a but not b.

    set_of_required_parameters = set(filter(lambda param: PARAMETERS[param]["required"], PARAMETERS.keys()))
    required_parameters_not_included = set_of_required_parameters - parameters_included

    if required_parameters_not_included:
        api_response = JSONAPIResponse()
        api_response.set_status(4, "Parameters missing: " + ", ".join(required_parameters_not_included))

        return api_response.build()

    # Checks if the parameters the user has included are valid

    parameter_is_valid = lambda parameter: re.match(PARAMETERS[parameter]["RegEx"], request.json[parameter])
    invalid_parameters = list(filter(lambda param: not parameter_is_valid(param), parameters_included))

    if invalid_parameters:
        api_response = JSONAPIResponse()
        api_response.set_status(6, "Parameters invalid: " + ", ".join(invalid_parameters))

        return api_response.build()

    # Checking if the username is not already in use.

    with DBConnection() as conn:
        query = "SELECT username FROM user ORDER BY username ASC;"
        username_records = conn.call(query)

    # Values come out in like so: ((username, ), ) so need to pull them out of the tuples

    usernames = [username_record[0] for username_record in username_records]

    if request.json["new_username"] in usernames:
        api_response = JSONAPIResponse()
        api_response.set_status(5, "Usename already exists")

        return api_response.build()

    with DBConnection() as conn:
        # Inserts the new user

        query = "INSERT INTO user(username) VALUES('{}');"
        query = query.format(request.json["new_username"])

        conn.call(query)

        user_id = conn.last_insert_id()

        # Generates a salt for the user's password, adds it to the end, hashes that hen stores it in the DB.

        password_salt = pw.generate_salt()
        salted_password_hash = pw.hash_string((request.json["new_password"] + password_salt))

        password_query = "INSERT INTO password(passwordHash, salt, userID) VALUES ('{}', '{}', {});"
        password_query = password_query.format(salted_password_hash, password_salt, str(user_id))

        conn.call(password_query)

        # Adds the extra parameters (if supplied)

        generic_query = "UPDATE user SET {SQL_column_name}='{value}' WHERE userID={sql_user_id};"

        if "email" in parameters_included:
            query = generic_query.format(
                SQL_column_name="emailAddress",
                value=request.json["email"],
                sql_user_id=str(user_id)
                )

            conn.call(query)

    api_response = JSONAPIResponse()
    return api_response.build()

@app.route("/login", methods=["POST"])
def login():
    if VERBOSE:
        print_posted_values(request)

    # Dict to store information about the parameters to be supplied

    PARAMETERS = {
        "username": {"RegEx":"^[\w\d]+$"},
        "password": {"RegEx": "^.{8,}$"}
        }

    # Checks if the required parameters are in included with difference of sets, gives items in a but not b

    parameters_not_included = set(PARAMETERS.keys()) - set(request.json.keys())

    if parameters_not_included:
        api_response = JSONAPIResponse()
        api_response.set_status(4, "Parameters missing: " + ", ".join(parameters_not_included))

        return api_response.build()

    # Checks if the parameters the user has included are valid

    parameter_is_valid = lambda parameter: re.match(PARAMETERS[parameter]["RegEx"], request.json[parameter])
    invalid_parameters = list(filter(lambda param: not parameter_is_valid(param), PARAMETERS.keys()))

    if invalid_parameters:
        api_response = JSONAPIResponse()
        api_response.set_status(6, "Parameters invalid: " + ", ".join(invalid_parameters))

        return api_response.build()

    # Checks if the user's password is the same as the salted and hashed one

    with DBConnection() as conn:
        query = "SELECT password.passwordHash, password.salt, user.userID FROM password INNER JOIN user ON password.userID = user.userID WHERE user.username = '{}';"
        query = query.format(request.json["username"])
        records = conn.call(query)

    if not records:
        api_response = JSONAPIResponse()
        api_response.set_status(8)

        return api_response.build()

    password_hash, salt, user_id = records[0][0], records[0][1], records[0][2]

    if not pw.hash_string(request.json["password"] + salt) == password_hash:
        api_response = JSONAPIResponse()
        api_response.set_status(7)

        return api_response.build()

    # Generates a session key for this session and stores it in the DB

    session_key = generate_session_key()

    current_date_and_time = datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S")

    with DBConnection() as conn:
        query = """INSERT INTO session(userID, sessionKey, sessionCreationTime, lastRequestTime)
        VALUES ({user_id}, '{session_key}', '{session_creation_time}', '{last_request_time}');"""

        query = query.format(
            user_id=user_id,
            session_key=session_key,
            session_creation_time=current_date_and_time,
            last_request_time=current_date_and_time)

        conn.call(query)

    api_response = JSONAPIResponse()
    api_response.add_content(session_key, "session_key")

    return api_response.build()

@app.route("/is_session_key_valid", methods=["POST"])
def check_if_session_key_valid():
    if VERBOSE:
        print_posted_values(request)

    # Checks if session key is present and valid

    if "session_key" not in request.json.keys():
        api_response = JSONAPIResponse()
        api_response.set_status(4, "Missing session_key")
        return api_response.build()

    api_response = JSONAPIResponse()
    is_valid = is_session_key_valid(request.json["session_key"])

    update_session_last_request_time(request.json["session_key"])

    if is_valid:
        is_valid = "true"
    else:
        is_valid = "false"

    api_response.add_content(is_valid, "is_valid")
    return api_response.build()

@app.route("/log_out", methods=["POST"])
def log_out():
    if VERBOSE:
        print_posted_values(request)

    # Checks if session key is present and valid

    if not "session_key" in request.json.keys():
            api_response = JSONAPIResponse()
            api_response.set_status(4, "Session key Missing.")
            return api_response.build()

    if not is_session_key_valid(request.json["session_key"]):
        api_response = JSONAPIResponse()
        api_response.set_status(6, "Session key not valid (not active or simply not a sessionKey). Your session may have expired, try logging in again.")
        return api_response.build()

    # Removes key from DB

    with DBConnection() as conn:
        query = "DELETE FROM session WHERE sessionKey='{}';"
        query = query.format(request.json["session_key"])
        conn.call(query)

    api_response = JSONAPIResponse()
    return api_response.build()

@app.route("/list_devices", methods=["POST"])
def list_devices():
    if VERBOSE:
        print_posted_values(request)

    # Checks if session key is present and valid

    if not "session_key" in request.json.keys():
            api_response = JSONAPIResponse()
            api_response.set_status(4, "Session key Missing.")
            return api_response.build()

    if not is_session_key_valid(request.json["session_key"]):
        api_response = JSONAPIResponse()
        api_response.set_status(6, "Session key not valid (not active or simply not a sessionKey)")
        return api_response.build()

    # Update the last request on the session key time

    update_session_last_request_time(request.json["session_key"])

    with DBConnection() as conn:
        query = """
        SELECT device.deviceID, device.name, user.username, deviceType.name
        FROM device
        INNER JOIN user on device.ownerID = user.userID
        INNER JOIN deviceType on device.typeID = deviceType.typeID
        """;

        device_records = conn.call(query)

    device_records_dict = [{"id": record[0], "name": record[1], "owner": record[2], "type": record[3]} for record in device_records]

    api_response = JSONAPIResponse()
    api_response.add_content(device_records_dict, "devices")

    return api_response.build()

@app.route("/get_device_info", methods=["POST"])
def get_device_info():
    if VERBOSE:
        print_posted_values(request)

    # Dict for info about what parameters are meant to be supplied to this function (apart from session_key)

    PARAMETERS = {
        "device_id": {"RegEx":"^[0-9]+$"}
        }

    # Checks if session key is present and valid

    if not "session_key" in request.json.keys():
            api_response = JSONAPIResponse()
            api_response.set_status(4, "Session key Missing.")
            return api_response.build()

    if not is_session_key_valid(request.json["session_key"]):
        api_response = JSONAPIResponse()
        api_response.set_status(6, "Session key not valid (not active or simply not a sessionKey)")
        return api_response.build()

    # Update the last request on the session key time

    update_session_last_request_time(request.json["session_key"])


    # Checks if the required parameters are in included with difference of sets, gives items in a but not b

    parameters_not_included = set(PARAMETERS.keys()) - set(request.json.keys())

    if parameters_not_included:
        api_response = JSONAPIResponse()
        api_response.set_status(4, "Parameters missing: " + ", ".join(parameters_not_included))

        return api_response.build()

    # Checks if the parameters the user has included are valid

    parameter_is_valid = lambda parameter: re.match(PARAMETERS[parameter]["RegEx"], request.json[parameter])
    invalid_parameters = list(filter(lambda param: not parameter_is_valid(param), PARAMETERS.keys()))

    if invalid_parameters:
        api_response = JSONAPIResponse()
        api_response.set_status(6, "Parameters invalid: " + ", ".join(invalid_parameters))

        return api_response.build()

    # Check the user has permission to do this action

    if not session_has_permission_for_device(request.json["session_key"], request.json["device_id"]):
        api_response = JSONAPIResponse()
        api_response.set_status(9)
        return api_response.build()

    # Pulls the details from the DB

    with DBConnection() as conn:
        query = """
        SELECT device.deviceID, device.name, user.username, deviceType.name
        FROM device
        INNER JOIN user on device.ownerID = user.userID
        INNER JOIN deviceType on device.typeID = deviceType.typeID
        WHERE device.deviceID = {};
        """;

        query = query.format(request.json["device_id"])

        device_records = conn.call(query)

    if not device_records:
        api_response = JSONAPIResponse()
        api_response.set_status(10)
        return api_response.build()

    record = device_records[0]

    device_dict = {"id": record[0], "name": record[1], "owner": record[2], "type": record[3]}

    api_response = JSONAPIResponse()
    api_response.add_content(device_dict, "device")

    return api_response.build()

@app.route("/add_device", methods=["POST"])
def add_device():
    if VERBOSE:
        print_posted_values(request)

    # Dict for info about what parameters are meant to be supplied to this function (apart from session_key)

    PARAMETERS = {
        "device_ip": {"RegEx":"^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$"},
        "auth_key": {"RegEx": "^[A-z0-9]{32}$"},
        "device_name": {"RegEx": "^(\w| )+$"}
        }

    # Checks if session key is present and valid

    if not "session_key" in request.json.keys():
            api_response = JSONAPIResponse()
            api_response.set_status(4, "Session key Missing.")
            return api_response.build()

    if not is_session_key_valid(request.json["session_key"]):
        api_response = JSONAPIResponse()
        api_response.set_status(6, "Session key not valid (not active or simply not a sessionKey)")
        return api_response.build()

    # Update the last request on the session key time

    update_session_last_request_time(request.json["session_key"])

    # Checks if the required parameters are in included with difference of sets, gives items in a but not b

    parameters_not_included = set(PARAMETERS.keys()) - set(request.json.keys())

    if parameters_not_included:
        api_response = JSONAPIResponse()
        api_response.set_status(4, "Parameters missing: " + ", ".join(parameters_not_included))

        return api_response.build()

    # Checks if the parameters the user has included are valid

    parameter_is_valid = lambda parameter: re.match(PARAMETERS[parameter]["RegEx"], request.json[parameter])
    invalid_parameters = list(filter(lambda param: not parameter_is_valid(param), PARAMETERS.keys()))

    if invalid_parameters:
        api_response = JSONAPIResponse()
        api_response.set_status(6, "Parameters invalid: " + ", ".join(invalid_parameters))

        return api_response.build()

    # Adding the device

    # Try to connect to the device, if not, return an error.
    try:
        conn =  DeviceConnection((request.json["device_ip"], DEVICE_PORT), request.json["auth_key"])

    except Exception as error:
        if VERBOSE:
            print("Error:")
            print(error)

        api_response = JSONAPIResponse()
        api_response.set_status(11, "Could not talk to the device, perhaps the IP is wrong.")
        return api_response.build()

    response = conn.call_command("enq")
    conn.close()

    if not response:
        # If this happens, the command call has timed out.

        api_response = JSONAPIResponse()
        api_response.set_status(11)
        return api_response.build()

    elif response["code"] == 1:
        # Invalid auth_key

        api_response = JSONAPIResponse()
        api_response.set_status(14)
        return api_response.build()

    elif response["code"] != 0: # Any other error
        if VERBOSE:
            print("Problem with device, code: " + str(response["code"]))

        api_response = JSONAPIResponse()
        api_response.set_status(13)
        return api_response.build()

    # Requesting the type from the device.

    try:
        conn =  DeviceConnection((request.json["device_ip"], DEVICE_PORT), request.json["auth_key"])

    except Exception as error:
        if VERBOSE:
            print("Error:")
            print(error)

        api_response = JSONAPIResponse()
        api_response.set_status(11)
        return api_response.build()

    response = conn.call_command("gtp")
    conn.close()

    if not response:
        # If this happens, the command call has timed out.

        api_response = JSONAPIResponse()
        api_response.set_status(12)
        return api_response.build()

    elif response["code"] != 0: # Any other error
        if VERBOSE:
            print("Problem with device, code: " + str(response["code"]))

        api_response = JSONAPIResponse()
        api_response.set_status(13)
        return api_response.build()

    # Putting the new device in the DB

    with DBConnection() as conn:
        query = """
        INSERT INTO device (ownerID, typeID, IP, name, authenticationKey)
        VALUES
        (
        (SELECT userID FROM session WHERE sessionKey = '{session_key}'),
        (SELECT typeID FROM deviceType WHERE name = '{device_type}'),
        '{device_ip}',
        '{device_name}',
        '{auth_key}'
        );
        """

        query = query.format(
            session_key = request.json["session_key"],
            device_type = response["type"],
            device_ip = request.json["device_ip"],
            device_name = request.json["device_name"],
            auth_key = request.json["auth_key"]
        )

        conn.call(query)

        query = """
        INSERT INTO permission (permissionTypeID, deviceID)
        VALUES
        (
        (SELECT typeID FROM permissionType WHERE name = 'disallow_all'),
        {}
        );
        """

        query = query.format(conn.last_insert_id())

        conn.call(query)

    api_response = JSONAPIResponse()
    return api_response.build()

@app.route("/call_command_on_device", methods=["POST"])
def call_command_on_device():
    if VERBOSE:
        print_posted_values(request)

    # Dict for info about what parameters are meant to be supplied to this function (apart from session_key)

    PARAMETERS = {
        "device_id": {"RegEx":"^[0-9]+$"},
        "command_code": {"RegEx": "^[a-z]{3}$"}
        }

    # Checks if session key is present and valid

    if not "session_key" in request.json.keys():
            api_response = JSONAPIResponse()
            api_response.set_status(4, "Session key Missing.")
            return api_response.build()

    if not is_session_key_valid(request.json["session_key"]):
        api_response = JSONAPIResponse()
        api_response.set_status(6, "Session key not valid (not active or simply not a sessionKey)")
        return api_response.build()

    # Update the last request on the session key time

    update_session_last_request_time(request.json["session_key"])

    # Checks if the required parameters are in included with difference of sets, gives items in a but not b

    parameters_not_included = set(PARAMETERS.keys()) - set(request.json.keys())

    if parameters_not_included:
        api_response = JSONAPIResponse()
        api_response.set_status(4, "Parameters missing: " + ", ".join(parameters_not_included))

        return api_response.build()

    # Checks if the parameters the user has included are valid

    parameter_is_valid = lambda parameter: re.match(PARAMETERS[parameter]["RegEx"], request.json[parameter])
    invalid_parameters = list(filter(lambda param: not parameter_is_valid(param), PARAMETERS.keys()))

    if invalid_parameters:
        api_response = JSONAPIResponse()
        api_response.set_status(6, "Parameters invalid: " + ", ".join(invalid_parameters))

        return api_response.build()


    # Pulling the device's IP and auth_key from the DB

    with DBConnection() as conn:
        query = "SELECT IP, authenticationKey FROM device WHERE deviceID = {};"
        query = query.format(request.json["device_id"])
        records = conn.call(query)

    if not records: # DeviceID doesn't exist
        api_response = JSONAPIResponse()
        api_response.set_status(16)
        return api_response.build()

    ip, auth_key = records[0]

    # Checking if the command code that the user has provided can be executed by said device

    with DBConnection() as conn:
        query = """
        SELECT command.commandCode FROM device
        INNER JOIN deviceType ON device.typeID = deviceType.typeID
        INNER JOIN deviceTypeHasCommand ON deviceType.typeID = deviceTypeHasCommand.typeID
        INNER JOIN command ON deviceTypeHasCommand.commandID = command.commandID
        WHERE device.deviceID = {};
        """

        query = query.format(request.json["device_id"])
        records = conn.call(query)

    if not records:
        api_response = JSONAPIResponse()
        api_response.set_status(17)
        return api_response.build()

    # Check the user has permission to do this action on this device

    if not session_has_permission_for_device(request.json["session_key"], request.json["device_id"]):
        api_response = JSONAPIResponse()
        api_response.set_status(9)
        return api_response.build()

    # Try to connect to the device using my DeviceConnection class, if not, return an error

    if VERBOSE:
        print("Connecting to: ")
        print(ip, DEVICE_PORT, auth_key)

    try:
        conn =  DeviceConnection((ip, DEVICE_PORT), auth_key)

    except Exception as error:

        """
        Could be considered bad practise not to specify an error, however
        there are simply too many errors that could occur here, they user can check
        in the logs later if they wish to do so.
        """

        if VERBOSE:
            print("Error:")
            print(error)

        api_response = JSONAPIResponse()
        api_response.set_status(11)
        return api_response.build()

    # Connection has been successfully established, now we send a command

    response = conn.call_command(request.json["command_code"])

    conn.close()

    if not response:
        # If this happens, the command call has timed out

        api_response = JSONAPIResponse()
        api_response.set_status(12)
        return api_response.build()

    if VERBOSE:
        print("Recieved from device:")
        print(json.dumps(response))

    """
    Although the device responded correctly, doesn't mean it executed the
    command correctly, the code below returns appropriate responses for such a
    situation.

    Only returns specific error codes for things that someone calling the API could have done wrong.
    The rest can be checked in the controller log.
    """

    if response["code"] != 0:
        if response["code"] == 3: # Invalid auth_key
            api_response = JSONAPIResponse()
            api_response.set_status(17)
            return api_response.build()

        else: # Any other problem that is irrelevent to an API user as if something went wrong, it was not their fault
            api_response = JSONAPIResponse()
            api_response.set_status(13)
            return api_response.build()

    del response["code"] # The caller need not know the device response code, only data it sends back (if any).

    api_response = JSONAPIResponse()

    if response:
        api_response.add_content(response, "device_response")

    return api_response.build()

@app.route("/get_device_permission_info", methods=["POST"])
def get_device_permission_info():
    if VERBOSE:
        print_posted_values(request)

    # Dict for info about what parameters are meant to be supplied to this function (apart from session_key)

    PARAMETERS = {
        "device_id": {"RegEx":"^[0-9]+$"}
        }

    # Checks if session key is present and valid

    if not "session_key" in request.json.keys():
            api_response = JSONAPIResponse()
            api_response.set_status(4, "Session key Missing.")
            return api_response.build()

    if not is_session_key_valid(request.json["session_key"]):
        api_response = JSONAPIResponse()
        api_response.set_status(6, "Session key not valid (not active or simply not a sessionKey)")
        return api_response.build()

    # Update the last request on the session key time

    update_session_last_request_time(request.json["session_key"])

    # Checks if the required parameters are in included with difference of sets, gives items in a but not b

    parameters_not_included = set(PARAMETERS.keys()) - set(request.json.keys())

    if parameters_not_included:
        api_response = JSONAPIResponse()
        api_response.set_status(4, "Parameters missing: " + ", ".join(parameters_not_included))

        return api_response.build()

    # Checks if the parameters the user has included are valid

    parameter_is_valid = lambda parameter: re.match(PARAMETERS[parameter]["RegEx"], request.json[parameter])
    invalid_parameters = list(filter(lambda param: not parameter_is_valid(param), PARAMETERS.keys()))

    if invalid_parameters:
        api_response = JSONAPIResponse()
        api_response.set_status(6, "Parameters invalid: " + ", ".join(invalid_parameters))

        return api_response.build()

    # Check the user has permission to do this action

    if not session_has_permission_for_device(request.json["session_key"], request.json["device_id"]):
        api_response = JSONAPIResponse()
        api_response.set_status(9)
        return api_response.build()

    # Pulling the permission type

    with DBConnection() as conn:
        query = "SELECT permissionType.name FROM permission INNER JOIN permissionType on permission.permissionTypeID = permissionType.typeID WHERE permission.deviceID = {};"
        query = query.format(request.json["device_id"])
        records = conn.call(query)

    if not records: # DeviceID must not exist
        api_response = JSONAPIResponse()
        api_response.set_status(16)
        return api_response.build()

    perm_type = records[0][0]

    # Pulling the users related to the permission from the DB

    with DBConnection() as conn:
        query = """
        SELECT user.username FROM permission
        INNER JOIN userInPermission ON permission.permissionID = userInPermission.permissionID
        INNER JOIN user on userInPermission.userID = user.userID
        INNER JOIN device ON permission.deviceID = device.deviceID
        WHERE permission.deviceID = {} AND NOT user.userID = device.ownerID;
        """

        query = query.format(request.json["device_id"])
        records = conn.call(query)

    usernames = [record[0] for record in records]

    permission = {
        "type": perm_type,
        "users": usernames
    }


    api_response = JSONAPIResponse()
    api_response.add_content(permission, "permission")
    return api_response.build()

@app.route("/get_permission_types", methods=["POST"])
def get_permission_types():
    # No parameters are sent here!

    with DBConnection() as conn:
        query = "SELECT name, description FROM permissionType;"
        records = conn.call(query)

    types = [{"name": record[0], "description": record[1]} for record in records]

    api_response = JSONAPIResponse()
    api_response.add_content(types, "types")
    return api_response.build()

@app.route("/get_users_list", methods=["POST"])
def get_users_list():
    # No parameters are sent here!

    with DBConnection() as conn:
        query = "SELECT username FROM user;"
        records = conn.call(query)

    users = [record[0] for record in records]

    api_response = JSONAPIResponse()
    api_response.add_content(users, "users")
    return api_response.build()

@app.route("/set_device_permission", methods=["POST"])
def set_device_permission():
    if VERBOSE:
        print_posted_values(request)

    # Dict for info about what parameters are meant to be supplied to this function (apart from session_key)

    PARAMETERS = {
        "device_id": {
            "RegEx":"^[0-9]+$",
            "isList": False
            },

        "permission_type": {
            "RegEx": "^\w+$",
            "isList": False
            },

        "users": {
            "RegEx": "^\w+$",
            "isList": True
            }
        }

    # Checks if session key is present and valid

    if not "session_key" in request.json.keys():
            api_response = JSONAPIResponse()
            api_response.set_status(4, "Session key Missing.")
            return api_response.build()

    if not is_session_key_valid(request.json["session_key"]):
        api_response = JSONAPIResponse()
        api_response.set_status(6, "Session key not valid (not active or simply not a sessionKey)")
        return api_response.build()

    # Update the last request on the session key time

    update_session_last_request_time(request.json["session_key"])

    # Checks if the required parameters are in included with difference of sets, gives items in a but not b

    parameters_not_included = set(PARAMETERS.keys()) - set(request.json.keys())

    if parameters_not_included:
        api_response = JSONAPIResponse()
        api_response.set_status(4, "Parameters missing: " + ", ".join(parameters_not_included))

        return api_response.build()

    # Checks if the parameters the user has included are valid

    parameter_is_valid = lambda parameter: re.match(PARAMETERS[parameter]["RegEx"], request.json[parameter])

    invalid_parameters = []

    for parameter in PARAMETERS.keys():
        if PARAMETERS[parameter]["isList"]:
            for value in request.json[parameter]:
                if not re.match(PARAMETERS[parameter]["RegEx"], value):
                    invalid_parameters.append(parameter)
                    break
        else:
            if not parameter_is_valid(parameter):
                invalid_parameters.append(parameter)


    if invalid_parameters:
        api_response = JSONAPIResponse()
        api_response.set_status(6, "Parameters invalid: " + ", ".join(invalid_parameters))

        return api_response.build()

    # Check the user has permission to do this action

    if not session_has_permission_for_device(request.json["session_key"], request.json["device_id"]):
        api_response = JSONAPIResponse()
        api_response.set_status(9)
        return api_response.build()

    # Pulling list of permission types

    with DBConnection() as conn:
        query = "SELECT name FROM permissionType ORDER BY name ASC;"
        records = conn.call(query)

    types = [record[0] for record in records]

    if not request.json["permission_type"] in types:
        api_response = JSONAPIResponse()
        api_response.set_status(6, "Not a valid permission type.")
        return api_response.build()

    # Check if all the users supplied actually exist

    with DBConnection() as conn:
        query = "SELECT username FROM user;"
        records = conn.call(query)

    users = [record[0] for record in records]

    for proposed_username in request.json["users"]:
        if not proposed_username in users:
            api_response = JSONAPIResponse()
            api_response.set_status(8)
            return api_response.build()

    # Removing the owner name if provided as no point having them in the permission

    with DBConnection() as conn:
        query = "SELECT user.username FROM session INNER JOIN user ON session.userID = user.userID WHERE session.sessionKey = '{}'"
        query = query.format(request.json["session_key"])
        records = conn.call(query)

    owner = records[0][0]

    if owner in request.json["users"]:
        request.json["users"].remove(owner)

    # Putting the permission in the DB

    with DBConnection() as conn:
        # Set permission type

        query = """
        UPDATE permission
        SET permission.permissionTypeID = (SELECT typeID FROM permissionType WHERE name = '{permission_type}')
        WHERE deviceID = {device_id};
        """

        query = query.format(
            permission_type = request.json["permission_type"],
            device_id = request.json["device_id"]
            )

        conn.call(query)

        # Remove all users related to permission

        query = "DELETE userInPermission FROM userInPermission INNER JOIN permission ON userInPermission.permissionID = permission.permissionID WHERE permission.deviceID = {};"
        query = query.format(request.json["device_id"])

        conn.call(query)

        # Add users user has sent

        query = """
        INSERT INTO userInPermission (userID, permissionID)
        VALUES
        ((SELECT userID FROM user WHERE username = '{username}'),
        (SELECT permissionID FROM permission WHERE deviceID = {device_id}));
        """

        for username in request.json["users"]:
            temp_query = query.format(
                username = username,
                device_id = request.json["device_id"]
                )

            conn.call(temp_query)

    api_response = JSONAPIResponse()
    return api_response.build()
