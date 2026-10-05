import { useState, useEffect } from 'react'
import './App.css'

const API_TIMEOUT = 5000 // 5 seconds

export function showError(message) {
  const dialog = document.getElementById('error-dialog')
  const msgEl = document.getElementById('error-dialog-message')
  if (dialog && msgEl) {
    msgEl.textContent = message
    dialog.showModal()
  } else {
    console.error(message)
  }
}

const api = {
  getDevices: async () => {
    try {
      return await window.pywebview.api.getDevices()
    } catch (err) {
      showError('Failed to get devices: ' + err)
      return []
    }
  },
  toggleMute: async (device_index) => {
    try {
      return await window.pywebview.api.toggleMute(device_index)
    } catch (err) {
      showError('Failed to toggle mute state: ' + err)
    }
  },
}

function App() {
  const [devices, setDevices] = useState([])
  const [loading, setLoading] = useState(true)

  // Function to fetch devices from backend
  const refreshDevices = async () => {
    const devices = await api.getDevices()
    setDevices(devices)
  }

  // Get devices from backend on mount
  useEffect(() => {
    const interval = setInterval(async () => {
      if (window.pywebview?.api) {
        clearInterval(interval)
        clearTimeout(timeout)
        await refreshDevices()
        setLoading(false)
      }
    }, 100)

    const timeout = setTimeout(() => {
      clearInterval(interval)
      setLoading(false)
      showError('Failed to connect to backend API within timeout: ' + API_TIMEOUT + 'ms')
    }, API_TIMEOUT)

    return () => {
      clearInterval(interval)
      clearTimeout(timeout)
    }
  }, [])

  // Accent color state and handler
  const [accentColor, setAccentColor] = useState('#ff0000')

  const handleColorChange = (e) => {
    const color = e.target.value
    setAccentColor(color)
    document.documentElement.style.setProperty('--accent', color)
    document.documentElement.style.setProperty('--accent-border', color)
  }



  return (
    <div className="app-container">
      <dialog id="error-dialog" className="error-dialog">
        <h3>Error</h3>
        <p id="error-dialog-message"></p>
        <button
          type="button"
          className="btn-dialog-close"
          onClick={() => document.getElementById('error-dialog')?.close()}
        >
          Close
        </button>
      </dialog>

      <header className="app-header">
        <h1>InputGate</h1>
        <div className="accent-control" title="Choose hover accent color">
          <input
            type="color"
            value={accentColor}
            onChange={handleColorChange}
            className="accent-swatch"
            aria-label="Accent color"
          />
        </div>
      </header>

      <main className="app-main">
        {loading && <p className="status-message">Scanning for devices...</p>}

        {!loading && devices.length === 0 && (
          <p className="status-message">No input devices detected.</p>
        )}

        <div className="device-list">
          {devices.map((device, index) => (
            <div key={device.id} className="device-card">
              <h3 className="device-name">{device.name}</h3>
              <div className="device-actions">
                <button
                  type="button"
                  className={`btn-toggle ${device.is_muted ? 'muted' : 'unmuted'}`}
                  onClick={async () => {
                    await api.toggleMute(index)
                    await refreshDevices()
                  }}>
                  {device.is_muted ? 'Unmute' : 'Mute'}
                </button>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}

export default App
