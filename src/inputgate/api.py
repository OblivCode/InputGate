from .models import InputDeviceGroup as BackendDevice
from .scanner import getDevices as getBackendDevicesFromScanner
from .muter import muteDevice, unmuteDevice, isMuted
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
    
    # Get the latest backend devices and convert them to frontend devices for the update
    backend_devices = getBackendDevices()
    frontend_devices = []
    for device in backend_devices:
        port = device.devices[0].physical_port

        frontend_devices.append(FrontendDevice(id=port, name=device.name, is_muted=isMuted(device)))

    # Update the global frontend devices list
    setFrontendDevices(frontend_devices)

    

# API class for the frontend
class InputGateApi:
    def getDevices(self) -> list[FrontendDevice]:
        """
        Returns a list of all input devices.
        """
        # Update the device groups with the latest devices from the scanner
        updateBackendDevices()

        # Parse backend device list to frontend device list
        updateFrontendDevices()

        return [asdict(d) for d  in getFrontendDevices()]

    def toggleMute(self, index: int) -> bool:
        """
        Toggles the mute state of the device with the given ID (physical port).
        Returns the updated boolean state.
        """
        # GEt devices and new value(inverted current value)
        devices = getFrontendDevices()
        b_devices = getBackendDevices()
        new_val = not devices[index].is_muted
        
        if new_val: # Mute
            if not muteDevice(b_devices[index]): # Mute fail
                new_val = False
        else: # Unmute
            if not unmuteDevice(b_devices[index]):
                # Unmute fail
                new_val = True
        devices[index].is_muted = new_val
        return new_val

