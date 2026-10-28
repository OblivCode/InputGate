# InputGate architecture

InputGate is a Linux desktop application. React calls the Python backend through
pywebview; Linux discovery and exclusive input grabs stay in their existing modules.

```text
app.py → InputGateApi → DeviceManager → scanner.py / muter.py
```

- `app.py` creates the manager, injects it into the API, and owns the window and
  frontend development server lifecycle.
- `api.py` exposes `getDevices()` and `toggleMute(device_id)` and forwards UI data
  from the manager. It owns no device registry or mute decisions.
- `manager.py` owns the latest scanned groups keyed by physical port, coordinates
  scanning and muting, and serializes those operations with a lock because bridge
  calls may run on separate threads. UI data is returned as fresh dictionaries.
- `scanner.py` reads `/proc/bus/input/devices`, groups nodes by physical port, and
  filters peripherals. `models.py` defines `Device` (a peripheral with an ID, name, nodes, and group ID)
  and `DeviceNode` (one Linux event node).
- `muter.py` owns open handles and Linux `EVIOCGRAB` operations. The manager reads
  mute state from it after each operation, including failures.

The frontend sends the physical-port ID, so scan reordering cannot redirect a
click to another device. IDs identify ports, not permanent hardware identities;
moving a peripheral to another port changes its ID. A refresh replaces the registry,
and toggling an unknown or removed ID raises an error through the bridge. Scanning
is request-driven; there is no hotplug watcher or background daemon. Existing grab
lifecycle and permission requirements remain unchanged.

## Verification

Run the application with `uv run inputgate` and check discovery and mute toggles
on a Linux desktop with input-device access. Automated tests are deferred.
