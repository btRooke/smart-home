import machine
import json
from utilities import *

from device import Device

class Switch(Device):
    def __init__(self, pin_number):
        # calls init of the device superclass.
        super().__init__()

        new_commands = {
            "tgl": self.toggle,
            "tof": self.open,
            "ton": self.close,
            "gcs": self.is_closed
        }

        self.type = "Switch"

        self.device_commands = merge_dicts(self.device_commands, new_commands)

        # Creates a pin object and specifies it is for output not inputself.
        self._pin = machine.Pin(pin_number, machine.Pin.OUT)

    def is_closed(self):
        return json.dumps({"code": 0, "state": str(self._pin.value())})

    def close(self):
        self._pin.value(1)
        return json.dumps({"code": 0})

    def open(self):
        self._pin.value(0)
        return json.dumps({"code": 0})

    def toggle(self):
        self._pin.value(not(self._pin.value()))
        return json.dumps({"code": 0})
