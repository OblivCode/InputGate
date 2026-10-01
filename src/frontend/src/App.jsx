import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [devices, setDevices] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchDevices = async () => {
      try {
        // Handle both camelCase and snake_case API exports from pywebview
        const fn = window.pywebview.api.getDevices || window.pywebview.api.get_devices
        const list = await fn()
        setDevices(list)
      } catch (err) {
        console.error('Failed to fetch devices:', err)
      } finally {
        setLoading(false)
      }
    }

    // Poll until pywebview.api is injected into the window object
    const interval = setInterval(() => {
      if (window.pywebview?.api) {
        clearInterval(interval)
        fetchDevices()
      }
    }, 50)

    // Fallback timeout: stop polling after 5 seconds if running outside pywebview
    const timeout = setTimeout(() => {
      clearInterval(interval)
      setLoading(false)
    }, 5000)

    // Cleanup timers on component unmount
    return () => {
      clearInterval(interval)
      clearTimeout(timeout)
    }
  }, [])

  const [accentColor, setAccentColor] = useState('#c084fc')

  const handleColorChange = (e) => {
    const color = e.target.value
    setAccentColor(color)
    document.documentElement.style.setProperty('--accent', color)
    document.documentElement.style.setProperty('--accent-border', color)
  }

  const handleToggleMute = async (deviceId) => {
    try {
      const fn = window.pywebview?.api?.toggleMute || window.pywebview?.api?.toggle_mute
      if (fn) {
        const isMuted = await fn(deviceId)
        setDevices((prev) =>
          prev.map((d) => (d.id === deviceId ? { ...d, is_muted: isMuted } : d))
        )
      }
    } catch (err) {
      console.error('Failed to toggle mute state:', err)
    }
  }

  return (
    <div className="app-container">
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
          {devices.map((device) => (
            <div key={device.id} className="device-card">
              <h3 className="device-name">{device.name}</h3>
              <div className="device-actions">
                <button
                  type="button"
                  className={`btn-toggle ${device.is_muted ? 'is-muted' : 'is-active'}`}
                  onClick={() => handleToggleMute(device.id)}
                >
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
