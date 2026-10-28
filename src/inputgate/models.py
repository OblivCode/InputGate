from dataclasses import dataclass


@dataclass
class DeviceNode:
    """One Linux input event node. Represents a single /dev/input/eventX file."""

    name: str
    event_path: str
    physical_port: str
    vendor: str = ""
    product: str = ""


@dataclass
class Device:
    """A physical peripheral and its event nodes."""

    # Physical-port ID; moving the peripheral to another port changes it.
    id: str
    name: str
    nodes: list[DeviceNode]
    # Vendor/name match group for this scan; -1 means unassigned.
    group_id: int = -1
