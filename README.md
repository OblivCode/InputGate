# InputGate ⚡

> Linux desktop utility built with React, Python, and Qt WebEngine for managing input devices.

InputGate is an open-source Linux peripheral manager that discovers input devices, groups their split USB endpoints into one physical device, and lets you mute them from a desktop UI.

---

## ✨ Features

- **Hardware topology grouping**: Groups split USB HID endpoints (mouse pointer, macros, consumer control, system control) into one device by physical port, using `/proc/bus/input/devices`.
- **Rootless device muting**: Silences devices at the kernel level with exclusive `EVIOCGRAB` grabs. If InputGate crashes or exits, the kernel releases the grab automatically.
- **Native desktop UI**: React and Vite inside a PyQt6 WebEngine window via `pywebview`.
- **One-command launch**: `uv run inputgate` starts the Vite dev server, opens the window, and cleans up the server on close.
- **Accent colour picker**: Choose the card hover colour from the header.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, `uv`, `pywebview`, `PySide6` (Qt WebEngine)
- **Frontend**: React, Vite, vanilla CSS

---

## 🚀 Build & Run

### Prerequisites

- [`uv`](https://docs.astral.sh/uv/)
- [Node.js](https://nodejs.org/) and npm
- Your user in the `input` group (needed to grab devices without root)

### Steps

```bash
git clone git@github.com:OblivCode/InputGate.git
cd InputGate
cd src/frontend && npm install && cd ../..
uv run inputgate
```

---

## 📁 Project Structure

```text
InputGate/
├── pyproject.toml
├── src/
│   ├── inputgate/
│   │   ├── app.py        # Window launcher and dev server lifecycle
│   │   ├── api.py        # pywebview bridge (frontend <-> backend)
│   │   ├── scanner.py    # Device discovery, filtering and port grouping
│   │   ├── muter.py      # EVIOCGRAB grab / ungrab handling
│   │   └── models.py     # InputDevice and InputDeviceGroup dataclasses
│   └── frontend/         # React + Vite UI
```

---

## 📝 TODO

- [ ] In-focus keyboard shortcuts: dynamic number keys to quickly toggle devices
- [ ] Dual-connection detection: spot the same peripheral connected over multiple ports (e.g. wireless dongle and USB cable) and warn or arbitrate
- [ ] Laptop keyboard auto-mute when an external keyboard is attached
- [ ] Cleaning / pet lock (one-click lock for all devices)

---

## 📄 License

MIT © [OblivCode](https://github.com/OblivCode)
