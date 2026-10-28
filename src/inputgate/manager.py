from dataclasses import dataclass
from threading import Lock

from . import muter, scanner
from .models import InputDeviceGroup


@dataclass(frozen=True)
class DeviceState:
    id: str
    name: str
    is_muted: bool


class DeviceManager:
    """Own the latest scan and coordinate Linux device mute operations.

    IDs are physical ports, stable across scan ordering, not across port moves.
    Serialize bridge calls so a refresh cannot replace the registry mid-toggle.
    """

    def __init__(self):
        self._devices: dict[str, InputDeviceGroup] = {}
        self._lock = Lock()

    def get_devices(self) -> list[DeviceState]:
        with self._lock:
            devices = scanner.getDevices()
            self._devices = {
                device.devices[0].physical_port: device for device in devices
            }
            return [
                DeviceState(device_id, device.name, muter.isMuted(device))
                for device_id, device in self._devices.items()
            ]

    def toggle_mute(self, device_id: str) -> bool:
        """Toggle a registered device and return its actual mute state.

        Unknown or removed IDs raise ValueError for the bridge to report.
        Failed mute operations leave the reported state with the muter.
        """
        with self._lock:
            if device_id not in self._devices:
                raise ValueError(f"Unknown device ID: {device_id}")
            device = self._devices[device_id]
            if muter.isMuted(device):
                muter.unmuteDevice(device)
            else:
                muter.muteDevice(device)
            return muter.isMuted(device)
