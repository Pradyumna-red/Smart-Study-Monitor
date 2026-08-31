import { useCallback, useEffect, useRef, useState } from 'react'
import { createEvent, initialEvents, monitoringApi, playWarningAlarm, prepareAlarms, stopWarningAlarms } from '../services/monitoringService'

const initialMetrics = { studyTime: 0, distractions: 0, phones: 0, sleepWarnings: 0 }

export function useMonitoringSession() {
  const [isMonitoring, setIsMonitoring] = useState(false)
  const [backendConnected, setBackendConnected] = useState(false)
  const [metrics, setMetrics] = useState(initialMetrics)
  const [events, setEvents] = useState(initialEvents)
  const [cameraError, setCameraError] = useState('')
  const streamRef = useRef(null)
  const videoRef = useRef(null)

  const addEvent = useCallback((message, type = 'system') => {
    setEvents((current) => [createEvent(message, type), ...current].slice(0, 8))
  }, [])

  const stopMonitoring = useCallback(async () => {
    stopWarningAlarms()
    streamRef.current?.getTracks().forEach((track) => track.stop())
    streamRef.current = null
    if (videoRef.current) videoRef.current.srcObject = null
    setIsMonitoring(false)
    setBackendConnected(false)
    try {
      const status = await monitoringApi.stopSession()
      setMetrics({ studyTime: status.study_time, distractions: status.distraction_count, phones: status.phone_detections, sleepWarnings: status.sleep_warnings })
      addEvent('MONITORING PAUSED', 'muted')
    } catch (error) {
      setCameraError(error.message)
    }
  }, [addEvent])

  const startMonitoring = useCallback(async () => {
    setCameraError('')
    try {
      if (!navigator.mediaDevices?.getUserMedia) throw new Error('This browser does not support webcam access.')
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false })
      prepareAlarms()
      streamRef.current = stream
      setIsMonitoring(true)
      setMetrics(initialMetrics)
      addEvent('CAMERA FEED CONNECTED', 'success')

      try {
        await monitoringApi.startSession()
        setBackendConnected(true)
        addEvent('FOCUS MODE ACTIVATED', 'success')
      } catch (error) {
        setBackendConnected(false)
        setCameraError(`${error.message} Camera preview is still available, but detection is paused.`)
        addEvent('BACKEND OFFLINE — DETECTION PAUSED', 'warning')
      }
    } catch (error) {
      setCameraError(error.message || 'Camera access was denied or is unavailable.')
      addEvent('MONITORING START FAILED', 'alert')
    }
  }, [addEvent])

  // The video element is rendered only after isMonitoring becomes true.
  // Attach the saved browser stream after React has mounted that element.
  useEffect(() => {
    if (!isMonitoring || !videoRef.current || !streamRef.current) return
    videoRef.current.srcObject = streamRef.current
    videoRef.current.play().catch(() => {})
  }, [isMonitoring])

  useEffect(() => {
    if (!isMonitoring) return undefined
    const timer = window.setInterval(() => {
      setMetrics((current) => ({ ...current, studyTime: current.studyTime + 1 }))
    }, 1000)
    return () => window.clearInterval(timer)
  }, [isMonitoring])

  useEffect(() => {
    if (!isMonitoring || !backendConnected) return undefined
    const timer = window.setInterval(() => {
      const video = videoRef.current
      if (!video || video.readyState < 2) return

      const canvas = document.createElement('canvas')
      canvas.width = 640
      canvas.height = 360
      canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height)
      canvas.toBlob(async (imageBlob) => {
        if (!imageBlob) return
        try {
          const result = await monitoringApi.analyzeFrame(imageBlob)
          const { metrics: apiMetrics } = result
          setMetrics({ studyTime: apiMetrics.study_time, distractions: apiMetrics.distraction_count, phones: apiMetrics.phone_detections, sleepWarnings: apiMetrics.sleep_warnings })
          addEvent(result.event, result.warning ? 'warning' : 'system')
          if (result.warning) await playWarningAlarm(result.warning)
        } catch (error) {
          setCameraError(error.message)
        }
      }, 'image/jpeg', 0.75)
    }, 2000)
    return () => window.clearInterval(timer)
  }, [isMonitoring, backendConnected, addEvent])

  useEffect(() => () => streamRef.current?.getTracks().forEach((track) => track.stop()), [])

  return { isMonitoring, metrics, events, cameraError, videoRef, startMonitoring, stopMonitoring }
}
