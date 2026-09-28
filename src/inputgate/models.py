from enum import Enum
from dataclasses import dataclass

@dataclass
class InputDevice:
    name: str
    event_path: str
    physical_port: str
    vendor: str = ""
    product: str = ""

@dataclass
class InputDeviceGroup:
    name: str
    devices: list[InputDevice]