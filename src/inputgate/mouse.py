import struct
from enum import Enum
from dataclasses import dataclass

# - Input event struct from <linux/input.h> -
# struct input_event {
#    struct timeval time;  // timestamp (seconds & microseconds)
#    __u16 type;           // 16-bit unsigned integer
#    __u16 code;           // 16-bit unsigned integer
#    __s32 value;          // 32-bit signed integer
#};

# The format of a 64-bit Linux input event:
# 
# 'l' = long (8 bytes) : seconds
# 'l' = long (8 bytes) : micro_seconds
# 'H' = unsigned short (2 bytes) : event_type
# 'H' = unsigned short (2 bytes) : event_code
# 'i' = signed int (4 bytes) : event_value

# Each variable
# seconds & micro_seconds -> the timestamp referring to the exact moment the event was triggered
# event_type -> the type of hardware action
# event_code -> specific action
# event_value -> the state or value


EVENT_FORMAT = "llHHi"


def getDeviceInfo(device_file: str):
    # Read data from device
    with open(device_file, "rb") as f:
        data = f.read(24)

    # Convert raw bytes to readable variables
    seconds, micro_seconds, event_type, event_code, event_value = struct.unpack(EVENT_FORMAT, data)

    print(f"Timestamp: {seconds}.{micro_seconds}")
    print(f"Type:  {event_type}")
    print(f"Code:  {event_code}")
    print(f"Value: {event_value}")


@dataclass
class InputDevice:
    name: str
    event_path: str
    physical_port: str
    vendor: str = ""
    product: str = ""

def getFieldFromDeviceBlock(block: str, field_name: str, field_prefix: str = None) -> str:
    if not field_name in block:
        return None

    # Get the start of the field value to the end of the line
    field_index_start = block.index(f"{field_name}") + len(f"{field_name}")
    field_index_end = block.index("\n", field_index_start)

    field = block[field_index_start:field_index_end].lstrip("=")

   
   # If quoted then return entire quoted string 
    if "\"" in field:
        field_index_end = field.index("\"", 1)
        field = field[:field_index_end + 1]
    else:
        field = field.split()
        # If a prefix is provided, find the first field that starts with that prefix
        if field_prefix:
            for f in field:
                if f.startswith(field_prefix):
                    field = f
                    break
            
        else: # If no prefix is provided, just take the first field
            field = field[0] if field else None

    # if field isn't a string or is empty for any reason, return None
    if type(field) is not str or not field:
        return None

    # Strip quotes if they exist
    field = field.strip("\"")
    return field
    

def scanInputDevices() -> list[InputDevice]:
    """
    Scans the system for available input devices.
    """
    # Read device blocks from /proc/bus/input/devices
    with open("/proc/bus/input/devices", "r") as f:
        # Each device block is separated by an empty line
        device_blocks: list[str] = f.read().split("\n\n")

    # Parse each device block to 'DeviceInput' objects
    input_devices: list[InputDevice] = []
    for block in device_blocks:
        # Skip empty blocks
        if not block.strip():
            continue

        # Get the physical port
        physical_port: str = getFieldFromDeviceBlock(block, "Phys")
        # Filter for input devices by requiring that the physical port contains "/input"
        if not physical_port or not "/input" in physical_port:
            continue
        # strip /input
        physical_port = physical_port.rsplit("/input")[0]

        # Get the vendor ID
        vendor: str =  getFieldFromDeviceBlock(block, "Vendor")
        # Filter out non-vendor and internal devices (Vendor 0000)
        if not vendor or vendor == "0000":
            continue

        # Get the rest
        product: str = getFieldFromDeviceBlock(block, "Product")   
        name: str = getFieldFromDeviceBlock(block, "Name")
        event_path: str = getFieldFromDeviceBlock(block, "Handlers", "event")

        # If name, phys and event_node are found, add them to the devices list
        if name and physical_port and event_path:
            input_devices.append(InputDevice(name=name, event_path=event_path, physical_port=physical_port, vendor=vendor, product=product))

    return input_devices

# ---
@dataclass
class InputDeviceGroup:
    name: str
    devices: list[InputDevice]

PERIPHERAL_KEYWORDS = ["mouse", "keyboard", "touchpad"]
def filterDevices(devices: list[InputDevice]) -> list[InputDevice]:
    """
    Filters the list of devices to include only those that are likely to be input peripherals."""
    # Whitelist keywords for peripherals
    

    filtered = []
    ports_to_ignore = []

    def append(device: InputDevice):
        filtered.append(device)
        ports_to_ignore.append(device.physical_port)

    for d in devices:
        # Ignore motherboard internal buttons (Vendor 0000)
        if d.physical_port in ports_to_ignore:
            continue

        # Check if the device name contains any of the peripheral keywords
        name_lower = d.name.lower()
        for keyword in PERIPHERAL_KEYWORDS:
            if keyword in name_lower:
                append(d)
                break

    return filtered

def hasSamePhysicalPort(*devices: InputDevice) -> bool:
    if len(devices) < 2:
        return True
    
    # Check if all ports are the same
    for i in range(1, len(devices)):
        if devices[i].physical_port != devices[0].physical_port:
            return False
    return True


def groupDevices(devices: list[InputDevice], device: InputDevice) -> InputDeviceGroup:
    """
    Groups an input device alongside other devices that share the same physical port.
    """
    group: list[InputDevice] = [device]

    for d in devices:
        if d != device and hasSamePhysicalPort(d, device):
            group.append(d)

    # Common prefix 
    # This implementation assumes the shortest name in the group is the common prefix, which may not always be accurate.
    prefix = group[0].name
    for i in range(1, len(group)):
        name = group[i].name
        
        if len(name) < len(prefix):
            prefix = name
            
    return InputDeviceGroup(name=prefix, devices=group)


# --

all_devices = scanInputDevices()
filtered_devices = filterDevices(all_devices)
devices = []

for d in filtered_devices:
    devices.append(groupDevices(all_devices, d))
    print(f"Device Group: {devices[-1].name}")