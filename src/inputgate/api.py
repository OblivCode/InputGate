

class InputGateApi:
    def get_devices(self) -> list:
        """
        Returns a list of all input devices.
        """
        return getInputDevices()