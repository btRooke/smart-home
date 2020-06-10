DROP DATABASE IF EXISTS controllerDB;
CREATE DATABASE controllerDB;
USE controllerDB;

CREATE TABLE user(
    userID INT UNSIGNED AUTO_INCREMENT NOT NULL UNIQUE,
    username VARCHAR(64) NOT NULL UNIQUE,
    emailAddress VARCHAR(256),
    PRIMARY KEY(userID)
);

CREATE TABLE password(
    passwordID INT UNSIGNED AUTO_INCREMENT NOT NULL,
    passwordHash VARCHAR(64) NOT NULL,
    salt varchar(16) NOT NULL,
    userID INT UNSIGNED NOT NULL UNIQUE,
    PRIMARY KEY (passwordID),
    CONSTRAINT `user_password_FK` FOREIGN KEY (userID) REFERENCES user(userID) ON DELETE CASCADE
);

CREATE TABLE session(
    sessionID INT UNSIGNED AUTO_INCREMENT NOT NULL,
    userID INT UNSIGNED NOT NULL,
    sessionKey VARCHAR(32) NOT NULL,
    sessionCreationTime DATETIME NOT NULL,
    lastRequestTime DATETIME NOT NULL,
    PRIMARY KEY(sessionID),
    CONSTRAINT `user_session_FK` FOREIGN KEY (userID) REFERENCES user(userID) ON DELETE CASCADE
);

CREATE TABLE deviceType(
    typeID INT UNSIGNED AUTO_INCREMENT NOT NULL,
    name VARCHAR(32),
    description VARCHAR(256),
    PRIMARY KEY(typeID)
);

CREATE TABLE device(
    deviceID INT UNSIGNED AUTO_INCREMENT NOT NULL,
    ownerID INT UNSIGNED NOT NULL,
    typeID INT UNSIGNED NOT NULL,
    IP VARCHAR(15), /* In form "xxx.xxx.xxx.xxx" */
    name VARCHAR(128),
    authenticationKey VARCHAR(32),
    PRIMARY KEY(deviceID),
    CONSTRAINT `device_owner_FK` FOREIGN KEY (ownerID) REFERENCES user(userID)  ON DELETE CASCADE,
    CONSTRAINT `device_type_FK` FOREIGN KEY (typeID) REFERENCES deviceType(typeID)  ON DELETE CASCADE
);

CREATE TABLE command(
    commandID INT UNSIGNED AUTO_INCREMENT NOT NULL,
    name VARCHAR(64),
    commandCode VARCHAR(3),
    description VARCHAR(512),
    PRIMARY KEY(commandID)
);

CREATE TABLE deviceTypeHasCommand(
    commandID INT UNSIGNED NOT NULL,
    typeID INT UNSIGNED NOT NULL,
    CONSTRAINT `linking_commandID_FK` FOREIGN KEY (commandID) REFERENCES command(commandID),
    CONSTRAINT `linking_deviceType_FK` FOREIGN KEY (typeID) REFERENCES deviceType(typeID),
    PRIMARY KEY(commandID, typeID)
);

CREATE TABLE permissionType(
    typeID INT UNSIGNED AUTO_INCREMENT NOT NULL,
    name VARCHAR(64),
    description VARCHAR(512),
    PRIMARY KEY(typeID)
);

CREATE TABLE permission(
    permissionID INT UNSIGNED AUTO_INCREMENT NOT NULL,
    permissionTypeID INT UNSIGNED NOT NULL,
    deviceID INT UNSIGNED NOT NULL UNIQUE,
    PRIMARY KEY(permissionID),
    CONSTRAINT `permission_type_FK` FOREIGN KEY (permissionTypeID) REFERENCES permissionType(typeID)  ON DELETE CASCADE,
    CONSTRAINT `permission_device_FK` FOREIGN KEY (deviceID) REFERENCES device(deviceID)  ON DELETE CASCADE
);

CREATE TABLE userInPermission(
    userInPermissionID INT UNSIGNED AUTO_INCREMENT NOT NULL,
    userID INT UNSIGNED NOT NULL,
    permissionID INT UNSIGNED NOT NULL,
    PRIMARY KEY(userInPermissionID),
    CONSTRAINT `user_in_permission_FK` FOREIGN KEY (userID) REFERENCES user(userID)  ON DELETE CASCADE,
    CONSTRAINT `permission_FK` FOREIGN KEY (permissionID) REFERENCES permission(permissionID)  ON DELETE CASCADE
);

INSERT INTO permissionType(name, description)
VALUES
('blacklist', 'Disallows all people on this list.'),
('whitelist', 'Allows only people on this list.'),
('disallow_all', 'Allows no one but owner.'),
('allow_all', 'Allows everyone.');

INSERT INTO deviceType(name, description)
VALUES
('Switch', 'A device which can be switched on and off via the control system.'),
('Thermometer', 'A device for viewing the temperature of wherever the device is placed.')
;

INSERT INTO command(name, commandCode, description)
VALUES
('Enquire', 'enq', 'Check to see if a device is still on the system.'),
('Validate Auth Key', 'val', 'Used upon adding a device to the system, asks a device to send its auth key to verify it what we think it is.'),
('Get Temperature', 'gtm', 'Gets the temprerature of a thermometer.'),
('Get Current State', 'gcs', 'Get the current state of a switch device.'),
('Toggle', 'tgl', 'Toggles the state of a switch device.'),
('Turn off', 'tof', 'Turns off (opens) a switch device.'),
('Turn on', 'ton', 'Turn on (closes) a switch device'),
('Get Type', 'gtp', 'Returns the type of a device.')
;

INSERT INTO deviceTypeHasCommand(commandID, typeID)
VALUES
((SELECT commandID FROM command WHERE commandCode = 'enq'), (SELECT typeID FROM deviceType WHERE name = 'Switch')),
((SELECT commandID FROM command WHERE commandCode = 'enq'), (SELECT typeID FROM deviceType WHERE name = 'Thermometer')),
((SELECT commandID FROM command WHERE commandCode = 'val'), (SELECT typeID FROM deviceType WHERE name = 'Switch')),
((SELECT commandID FROM command WHERE commandCode = 'val'), (SELECT typeID FROM deviceType WHERE name = 'Thermometer')),
((SELECT commandID FROM command WHERE commandCode = 'gtm'), (SELECT typeID FROM deviceType WHERE name = 'Thermometer')),
((SELECT commandID FROM command WHERE commandCode = 'tgl'), (SELECT typeID FROM deviceType WHERE name = 'Switch')),
((SELECT commandID FROM command WHERE commandCode = 'tof'), (SELECT typeID FROM deviceType WHERE name = 'Switch')),
((SELECT commandID FROM command WHERE commandCode = 'ton'), (SELECT typeID FROM deviceType WHERE name = 'Switch')),
((SELECT commandID FROM command WHERE commandCode = 'gcs'), (SELECT typeID FROM deviceType WHERE name = 'Switch')),
((SELECT commandID FROM command WHERE commandCode = 'gtp'), (SELECT typeID FROM deviceType WHERE name = 'Switch')),
((SELECT commandID FROM command WHERE commandCode = 'gtp'), (SELECT typeID FROM deviceType WHERE name = 'Thermometer'))
;
