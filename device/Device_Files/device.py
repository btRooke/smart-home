import json

class Device:
    def __init__(self):
        self.type = "Not Assigned"
        self.device_commands = {
            "enq": self.enquire,
            "gtp": self.get_type
        }

    def enquire(self):
        return json.dumps({"code": 0})

    def get_type(self):
        return json.dumps({"code": 0, "type": self.type})
