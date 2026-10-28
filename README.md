# InputGate

InputGate is a Linux desktop utility for discovering and muting input peripherals.
It groups event nodes by physical port and lets you mute each device from a React
interface hosted by pywebview and PySide6.

## Requirements

- Linux with `/proc/bus/input/devices` and `/dev/input/event*`.
- Python 3.10+ and [uv](https://docs.astral.sh/uv/).
- Node.js and npm to build the frontend or run the development server.
- Read access to the input event nodes. This is commonly granted through the
  `input` group, depending on the system configuration.

## Installation

```bash
git clone https://github.com/OblivCode/InputGate.git
cd InputGate
uv sync
cd src/frontend
npm install
npm run build
cd ../..
```

## Usage

Start the desktop application with the built frontend:

```bash
uv run inputgate
```

Mute or unmute a peripheral using its device card. Each action applies to all
of that peripheral's grouped event nodes.

## Behaviour

Discovery reads `/proc/bus/input/devices`, groups nodes by physical port, and
filters peripherals by name. Vendor and name matches also receive a group ID.

Muting uses Linux `EVIOCGRAB` to exclusively grab a device's event nodes.
Unmuting releases those grabs. Closing the process releases its open handles.

Device IDs represent physical ports. Scan ordering does not change them, but
moving a device to another port does. Discovery runs when the UI requests devices;
there is no background hotplug watcher.

## Verification and limitations

Check that the expected peripherals appear and that mute and unmute affect the
intended device. Actual grabbing requires input-device access. Automated tests
are deferred.

Discovery currently depends on physical-port data and peripheral names. Matching
vendor and name groups does not apply automatic priority rules. Muting is manual;
there is no recovery timer or cleaning lock yet.

See [architecture](docs/architecture.md) for module responsibilities and design
constraints.

## Development

Run with the Vite development server:

```bash
uv run inputgate --dev
```

`startDev()` starts Vite and stops it when the window closes. `start()` loads
`src/frontend/dist/index.html` without starting Vite. Rebuild the frontend after
changes when using the normal launch command. These commands run from a source
checkout; standalone distribution is not configured.

Frontend checks are available in `src/frontend`:

```bash
npm run lint
npm run build
```

Functions use `fooBar()`, variables use `foo_bar`, and classes use `FooBar`.
Internal helpers use a leading underscore. Keep comments concise and explain
meaning, assumptions, or non-obvious behaviour.

## Roadmap

- Keyboard shortcuts for device toggles.
- Dual-connection detection and priority handling.
- Laptop keyboard muting when an external keyboard is connected.
- A timed cleaning lock.

## License

[MIT](LICENSE) © OblivCode.
