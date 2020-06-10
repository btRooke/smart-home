import machine
import json
from utilities import *

from device import Device

class Thermometer(Device):
    def __init__(self, pin_number):
        # calls init of the device superclass.
        super().__init__()

        new_commands = {
            "gtm": self.get_temperature,
        }

        self.type = "Thermometer"

        self.device_commands = merge_dicts(self.device_commands, new_commands)

        # Creates an analog to digital conversion pin
        self._pin = machine.ADC(pin_number)

    def get_temperature(self):
        """
        When _pin.read() is called, a value between 1024 and 0 gets returned,
        this can be scaled to return a temperature.

        500 reading are taken and a mean is found as the temperature fluxtates
        on single readings. This gives a nice, accurate value.
        """

        temperature = sum([(self._pin.read()/1024) * 3300 * 0.1 for i in range(500)])/500

        return json.dumps({"code": 0, "temperature": temperature})
