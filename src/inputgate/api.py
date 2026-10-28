from dataclasses import asdict

from .manager import DeviceManager


class InputGateApi:
    """Expose device operations to the pywebview frontend."""

    def __init__(self, manager: DeviceManager):
        self._manager = manager

    def getDevices(self) -> list[dict]:
        return [asdict(device) for device in self._manager.get_devices()]

    def toggleMute(self, device_id: str) -> bool:
        return self._manager.toggle_mute(device_id)
