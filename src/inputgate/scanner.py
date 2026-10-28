from .models import DeviceNode, Device

PERIPHERAL_KEYWORDS = ["mouse", "keyboard", "touchpad"]

def _getFieldFromDeviceBlock(block: str, field_name: str, field_prefix: str = None) -> str:
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

def _hasSamePhysicalPort(*devices: DeviceNode) -> bool:
    if len(devices) < 2:
        return True

    # Check if all ports are the same
    for i in range(1, len(devices)):
        if devices[i].physical_port != devices[0].physical_port:
            return False
    return True
#

def _scanDeviceNodes() -> list[DeviceNode]:
    """Scan Linux input event nodes."""
    # Read device blocks from /proc/bus/input/devices
    with open("/proc/bus/input/devices", "r") as f:
        # Each device block is separated by an empty line
        device_blocks: list[str] = f.read().split("\n\n")

    # Parse each device block into a node
    input_devices: list[DeviceNode] = []
    for block in device_blocks:
        # Skip empty blocks
        if not block.strip():
            continue

        # Get the physical port
        physical_port: str = _getFieldFromDeviceBlock(block, "Phys")
        # Filter for input devices by requiring that the physical port contains "/input"
        if not physical_port or not "/input" in physical_port:
            continue
        # strip /input
        physical_port = physical_port.rsplit("/input")[0]

        # Get the vendor ID
        vendor: str =  _getFieldFromDeviceBlock(block, "Vendor")
        # Filter out non-vendor and internal devices (Vendor 0000)
        if not vendor or vendor == "0000":
            continue

        # Get the rest
        product: str = _getFieldFromDeviceBlock(block, "Product")
        name: str = _getFieldFromDeviceBlock(block, "Name")
        event_path: str = _getFieldFromDeviceBlock(block, "Handlers", "event")

        # If name, phys and event_node are found, add them to the devices list
        if name and physical_port and event_path:
            input_devices.append(DeviceNode(name=name, event_path=event_path, physical_port=physical_port, vendor=vendor, product=product))

    return input_devices

def _groupDevices(devices: list[DeviceNode]) -> list[Device]:
    """Group nodes by physical port."""
    group: dict[str, Device] = {}

    def _append(device: DeviceNode):
        if device.physical_port in group:
            # Add to existing group
            group[device.physical_port].nodes.append(device)
            # Update the group name if the new device has a shorter name
            if len(device.name) < len(group[device.physical_port].name):
                group[device.physical_port].name = device.name
        else:
            # Create new group
            group[device.physical_port] = Device(id=device.physical_port, name=device.name, nodes=[device])

    for d in devices:
        _append(d)

    return list(group.values())




def _filterDevices(groups: list[Device]) -> list[Device]:
    """Keep input peripherals."""
    filtered: list[Device] = []

    for group in groups:
        # Check if any device in the group matches peripheral keywords
        is_peripheral = False
        for device in group.nodes:
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

def _splitDevicesByMatch(devices: list[Device]) -> list[Device]:
    """Assign group IDs using vendor and name matches."""
    groups: list[str] = [] # vendor + name
    for i in range(0, len(devices)):
        d1 = devices[i]
        d_name = d1.nodes[0].vendor + d1.name
        matched = False

        for j  in range(0, len(groups)):
            group = groups[j]
            if d_name in group or group in d_name:
                matched = True
                # Assign device to group
                d1.group_id = j

                # SHorter name should act as matching substring
                if len(d_name) < len(group):
                    groups[j] = d_name

                break
        # If no match was found, create a new group
        if not matched:
            groups.append(d_name)
            d1.group_id = len(groups) - 1
    return devices




def getDevices() -> list[Device]:
    """Return peripherals grouped by physical port."""
    # Scan for input devices
    all_devices: list[DeviceNode] = _scanDeviceNodes()
    # Group input devices by physical port
    devices: list[Device] = _groupDevices(all_devices)
    # Filter input device groups for peripherals
    filtered_devices: list[Device] = _filterDevices(devices)
    # Split devices into lists by matching vendor IDs and names
    matched_devices = _splitDevicesByMatch(filtered_devices)
    return matched_devices
