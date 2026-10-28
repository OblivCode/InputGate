from threading import Lock

from . import muter, scanner
from .models import Device


class DeviceManager:
    """Own the device registry and coordinate scanning and muting."""

    def __init__(self):
        # Maps physical-port IDs to the latest scanned devices.
        self._devices: dict[str, Device] = {}
        # Bridge calls run on separate threads; keep scans and toggles from overlapping.
        self._lock = Lock()

    def getDevices(self) -> list[dict]:
        """Refresh devices and return their UI data."""
        with self._lock:
            self._devices = {device.id: device for device in scanner.getDevices()}
            return [
                {"id": device.id, "name": device.name,
                 "is_muted": muter.isMuted(device)}
                for device in self._devices.values()
            ]

    def toggleMute(self, device_id: str) -> bool:
        """Toggle a known device and return its mute state."""
        with self._lock:
            if device_id not in self._devices:
                raise ValueError(f"Unknown device ID: {device_id}")
            device = self._devices[device_id]
            if muter.isMuted(device):
                muter.unmuteDevice(device)
            else:
                muter.muteDevice(device)
            # Read the actual state, including when a grab or release fails.
            return muter.isMuted(device)
