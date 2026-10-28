from .manager import DeviceManager


class InputGateApi:
    """Expose device operations to the pywebview frontend."""

    def __init__(self, manager: DeviceManager):
        self._manager = manager

    def getDevices(self) -> list[dict]:
        return self._manager.getDevices()

    def toggleMute(self, device_id: str) -> bool:
        return self._manager.toggleMute(device_id)
