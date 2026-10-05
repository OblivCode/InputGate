from .models import InputDeviceGroup
import fcntl
from io import BufferedReader

# EVIOCGRAB ioctl request code for 64-bit Linux:
# _IOW('E', 0x90, int) -> 0x40044590
EVIOCGRAB = 0x40044590

# Maps physical_port -> list of open file handles
_active_grabs: dict[str, list[BufferedReader]] = {}

def muteDevice(device: InputDeviceGroup) -> bool:
    port: str = device.devices[0].physical_port

    # If in active grab, its already muted
    if port in _active_grabs:
        return True

    handles: list[BufferedReader] = []
    try:
        for node in device.devices:
            # Open the /dev/input/eventX device file
            f = open(f"/dev/input/{node.event_path}", "rb")
            # Issue exclusive grab (1)
            fcntl.ioctl(f.fileno(), EVIOCGRAB, 1)
            handles.append(f)
        # Save handles
        _active_grabs[port] = handles
        return True
    except Exception as e:
        print(f"Failed to mute {device.name}: {e}")
        print("Releasing any handles...")
        # Release any handles
        for f in handles:
            try:
                fcntl.ioctl(f.fileno(), EVIOCGRAB, 0)
                f.close()
            except OSError:
                print(f"Failed to release handle: " + f.name)
        # 
        print("\n")
        return False
    
    
     

def unmuteDevice(device: InputDeviceGroup) -> bool:
    port: str = device.devices[0].physical_port

    # If not in active grab, its already unmuted
    if port not in _active_grabs:
        return True

    # Release handles
    handles: list[BufferedReader] = _active_grabs[port]
    len_before = len(handles)
    try:
        for f in handles[:]:
            fcntl.ioctl(f.fileno(), EVIOCGRAB, 0)
            f.close()
            handles.remove(f)
        # Remove from active grabs
        del _active_grabs[port]
        return True
    except Exception as e:
        print(f"Failed to unmute {device.name}: {e}")
        print(f"Remaining handles: {len(handles)}/{len_before}")
        return False
    

def isMuted(device: InputDeviceGroup) -> None:
    port: str = device.devices[0].physical_port
    return port in _active_grabs