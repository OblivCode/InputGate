from .models import InputDeviceGroup as BackendDevice
from .scanner import getDevices as getBackendDevicesFromScanner
from dataclasses import dataclass, asdict

@dataclass
class FrontendDevice:
    id: str # physical port
    name: str 
    is_muted: bool = False

_backend_devices: list[BackendDevice] = []
_frontend_devices: list[FrontendDevice] = []

# Setters and getters for the global variables
def setBackendDevices(devices: list[BackendDevice]):
    global _backend_devices
    _backend_devices = devices
def getBackendDevices() -> list[BackendDevice]:
    return _backend_devices

def setFrontendDevices(devices: list[FrontendDevice]):
    global _frontend_devices
    _frontend_devices = devices
def getFrontendDevices() -> list[FrontendDevice]:
    return _frontend_devices

# API helper functions
def updateBackendDevices():
    """
    Updates the global backend devices list with the latest devices from the scanner.
    """
    setBackendDevices(getBackendDevicesFromScanner())
def updateFrontendDevices():
    """
    Converts a list of InputDeviceGroup objects to a list of Device objects.
    """
    # Get states of current frontend devices and save the muted ones
    devices = getFrontendDevices()
    muted_devices: list[str] = [d.id for d in filter(lambda d: d.is_muted, devices)]
    
    # Get the latest backend devices and convert them to frontend devices for the update
    backend_devices = getBackendDevices()
    frontend_devices = []
    for i in range(len(backend_devices)):
        b_d = backend_devices[i]
        port = b_d.devices[0].physical_port

        frontend_devices.append(FrontendDevice(id=port, name=b_d.name, is_muted=port in muted_devices))

    # Update the global frontend devices list
    setFrontendDevices(frontend_devices)

    

# API class for the frontend
class InputGateApi:
    def get_devices(self) -> list[FrontendDevice]:
        """
        Returns a list of all input devices.
        """
        # Update the device groups with the latest devices from the scanner
        updateBackendDevices()

        # Parse backend device list to frontend device list
        updateFrontendDevices()

        return [asdict(d) for d  in getFrontendDevices()]

    def toggle_mute(self, device_id: str) -> bool:
        """
        Toggles the mute state of the device with the given ID (physical port).
        Returns the updated boolean state.
        """
        devices = getFrontendDevices()
        for d in devices:
            if d.id == device_id:
                d.is_muted = not d.is_muted
                return d.is_muted
        return False

