const timestamp = () => new Date().toLocaleTimeString('en-GB', { hour12: false })
const API_URL = 'http://127.0.0.1:8000'
const alarms = {
  'FACE NOT DETECTED': new Audio(`${API_URL}/audio/face`),
  'SLEEP WARNING': new Audio(`${API_URL}/audio/sleep`),
  'PHONE DETECTED': new Audio(`${API_URL}/audio/phone`),
}

export const createEvent = (message, type = 'system') => ({ id: crypto.randomUUID(), time: timestamp(), message, type })

export const initialEvents = [
  createEvent('DASHBOARD READY', 'system'),
]

export function prepareAlarms() {
  Object.values(alarms).forEach((alarm) => alarm.load())
}

export async function playWarningAlarm(warning) {
  const selectedAlarm = alarms[warning]
  if (!selectedAlarm || !selectedAlarm.paused) return

  Object.values(alarms).forEach((alarm) => {
    if (alarm !== selectedAlarm) {
      alarm.pause()
      alarm.currentTime = 0
    }
  })
  selectedAlarm.currentTime = 0
  await selectedAlarm.play()
}

export function stopWarningAlarms() {
  Object.values(alarms).forEach((alarm) => {
    alarm.pause()
    alarm.currentTime = 0
  })
}

async function request(path, options = {}) {
  let response
  try {
    response = await fetch(`${API_URL}${path}`, options)
  } catch {
    throw new Error('Cannot reach the backend. Start FastAPI on port 8000.')
  }

  const data = await response.json()
  if (!response.ok) throw new Error(data.detail || 'The backend request failed.')
  return data
}

export const monitoringApi = {
  startSession: () => request('/monitor/start', { method: 'POST' }),
  stopSession: () => request('/monitor/stop', { method: 'POST' }),
  getStatus: () => request('/monitor/status'),
  analyzeFrame: (imageBlob) => {
    const formData = new FormData()
    formData.append('frame', imageBlob, 'frame.jpg')
    return request('/monitor/analyze', { method: 'POST', body: formData })
  },
}
