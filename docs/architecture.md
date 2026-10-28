# InputGate architecture

InputGate is a Linux desktop application. React calls the Python backend through
pywebview; Linux discovery and exclusive input grabs stay in their existing modules.

```text
app.py → InputGateApi → DeviceManager → scanner.py / muter.py
```

- `app.py` creates the manager, injects it into the API, and owns the window and
  frontend development server lifecycle.
- `api.py` exposes `getDevices()` and `toggleMute(device_id)` and serializes device
  snapshots for the bridge. It owns no device registry or mute decisions.
- `manager.py` owns the latest scanned groups keyed by physical port, coordinates
  scanning and muting, and serializes those operations with a lock because bridge
  calls may run on separate threads. Returned snapshots are immutable.
- `scanner.py` reads `/proc/bus/input/devices`, groups nodes by physical port, and
  filters peripherals. `models.py` holds the existing hardware dataclasses.
- `muter.py` owns open handles and Linux `EVIOCGRAB` operations. The manager reads
  mute state from it after each operation, including failures.

The frontend sends the physical-port ID, so scan reordering cannot redirect a
click to another device. IDs identify ports, not permanent hardware identities;
moving a peripheral to another port changes its ID. A refresh replaces the registry,
and toggling an unknown or removed ID raises an error through the bridge. Scanning
is request-driven; there is no hotplug watcher or background daemon. Existing grab
lifecycle and permission requirements remain unchanged.

## Verification

Run `PYTHONPATH=src python -m unittest discover -s tests` from the repository root.
The focused tests replace discovery and grab operations with fakes and require no
input-device permissions or GUI installation. Run `npm run lint` and `npm run build`
in `src/frontend` after installing its dependencies. Actual device grabbing needs
manual verification on a Linux desktop with input-device access.
