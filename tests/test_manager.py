import unittest
from unittest.mock import patch

from inputgate.api import InputGateApi
from inputgate.manager import DeviceManager
from inputgate.models import InputDevice, InputDeviceGroup


def group(port):
    return InputDeviceGroup(port, [InputDevice(port, 'event1', port)])


class DeviceManagerTests(unittest.TestCase):
    def setUp(self):
        self.first, self.second = group('usb-1'), group('usb-2')
        self.muted = set()
        self.scan = patch('inputgate.manager.scanner.getDevices',
                          return_value=[self.first, self.second]).start()
        self.mute = patch('inputgate.manager.muter.muteDevice',
                          side_effect=self.grab).start()
        self.unmute = patch('inputgate.manager.muter.unmuteDevice',
                            side_effect=self.release).start()
        patch('inputgate.manager.muter.isMuted',
              side_effect=lambda d: d.devices[0].physical_port in self.muted).start()
        self.addCleanup(patch.stopall)
        self.manager = DeviceManager()

    def grab(self, device):
        self.muted.add(device.devices[0].physical_port)
        return True

    def release(self, device):
        self.muted.discard(device.devices[0].physical_port)
        return True

    def test_id_targets_same_device_after_scan_reordering(self):
        self.manager.get_devices()
        self.scan.return_value = [self.second, self.first]
        self.manager.get_devices()
        self.assertTrue(self.manager.toggle_mute('usb-1'))
        self.mute.assert_called_once_with(self.first)
        self.assertFalse(self.manager.toggle_mute('usb-1'))
        self.unmute.assert_called_once_with(self.first)

    def test_refresh_removes_stale_ids(self):
        self.manager.get_devices()
        self.scan.return_value = [self.second]
        self.manager.get_devices()
        with self.assertRaises(ValueError):
            self.manager.toggle_mute('usb-1')
        self.mute.assert_not_called()
        self.unmute.assert_not_called()

    def test_unknown_id_before_scan(self):
        with self.assertRaises(ValueError):
            self.manager.toggle_mute('usb-missing')
        self.mute.assert_not_called()

    def test_failures_report_actual_state(self):
        self.manager.get_devices()
        self.mute.side_effect = None
        self.mute.return_value = False
        self.assertFalse(self.manager.toggle_mute('usb-1'))
        self.muted.add('usb-1')
        self.unmute.side_effect = None
        self.unmute.return_value = False
        self.assertTrue(self.manager.toggle_mute('usb-1'))

    def test_refresh_reads_live_mute_state(self):
        before = self.manager.get_devices()
        self.muted.add('usb-1')
        after = self.manager.get_devices()
        self.assertFalse(before[0].is_muted)
        self.assertTrue(after[0].is_muted)
        self.scan.return_value = []
        self.assertEqual(self.manager.get_devices(), [])

    def test_managers_have_independent_registries(self):
        self.manager.get_devices()
        with self.assertRaises(ValueError):
            DeviceManager().toggle_mute('usb-1')

    def test_api_serializes_and_delegates_by_id(self):
        api = InputGateApi(self.manager)
        self.assertEqual(api.getDevices(), [
            {'id': 'usb-1', 'name': 'usb-1', 'is_muted': False},
            {'id': 'usb-2', 'name': 'usb-2', 'is_muted': False},
        ])
        self.assertTrue(api.toggleMute('usb-2'))
        self.mute.assert_called_once_with(self.second)
        with self.assertRaises(ValueError):
            api.toggleMute('missing')


if __name__ == '__main__':
    unittest.main()
