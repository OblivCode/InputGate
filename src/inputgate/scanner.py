from .models import InputDevice, InputDeviceGroup

PERIPHERAL_KEYWORDS = ["mouse", "keyboard", "touchpad"]

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

def hasSamePhysicalPort(*devices: InputDevice) -> bool:
    if len(devices) < 2:
        return True
    
    # Check if all ports are the same
    for i in range(1, len(devices)):
        if devices[i].physical_port != devices[0].physical_port:
            return False
    return True
#

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

def groupDevices(devices: list[InputDevice]) -> list[InputDeviceGroup]:
    """
    Groups an input device alongside other devices that share the same physical port.
    """
    group: dict[str, InputDeviceGroup] = {}

    def append(device: InputDevice):
        if device.physical_port in group:
            # Add to existing group
            group[device.physical_port].devices.append(device)
            # Update the group name if the new device has a shorter name
            if len(device.name) < len(group[device.physical_port].name):
                group[device.physical_port].name = device.name
        else:
            # Create new group
            group[device.physical_port] = InputDeviceGroup(name=device.name, devices=[device]) 

    for d in devices:
        append(d)
    
    return list(group.values())




def filterDevices(groups: list[InputDeviceGroup]) -> list[InputDeviceGroup]:
    """
    Filters device groups to include only input peripherals.
    """
    filtered: list[InputDeviceGroup] = []

    for group in groups:
        # Check if any device in the group matches peripheral keywords
        is_peripheral = False
        for device in group.devices:
            name_lower = device.name.lower()
            for keyword in PERIPHERAL_KEYWORDS:
                if keyword in name_lower:
                    is_peripheral = True
                    break
            if is_peripheral:
                break

        # If it is a peripheral, keep the group
        if is_peripheral:
            filtered.append(group)

    return filtered


def getDevices() -> list[InputDeviceGroup]:
    """
    Returns a list of all input devices grouped by physical port.
    """
    # Scan for input devices
    all_devices: list[InputDevice] = scanInputDevices()
    # Group input devices by physical port
    devices: list[InputDeviceGroup] = groupDevices(all_devices)
    # Filter input device groups for peripherals
    filtered_devices: list[InputDeviceGroup] = filterDevices(devices)
    return filtered_devices

    