import { useMonitoringSession } from './hooks/useMonitoringSession'
import { Header } from './components/Header'
import { CameraFeed } from './components/CameraFeed'
import { MetricsGrid } from './components/MetricsGrid'
import { EventLog } from './components/EventLog'
import { ControlPanel } from './components/ControlPanel'
import { FocusStatus } from './components/FocusStatus'

export default function App() {
  const session = useMonitoringSession()

  return (
    <main className="app-shell">
      <div className="background-grid" aria-hidden="true" />
      <div className="ambient-glow glow-one" aria-hidden="true" />
      <div className="ambient-glow glow-two" aria-hidden="true" />
      <div className="dashboard">
        <Header isMonitoring={session.isMonitoring} />
        <section className="dashboard-layout">
          <div className="primary-column">
            <FocusStatus isMonitoring={session.isMonitoring} />
            <CameraFeed
              isMonitoring={session.isMonitoring}
              videoRef={session.videoRef}
              cameraError={session.cameraError}
              onStart={session.startMonitoring}
              onStop={session.stopMonitoring}
            />
            <MetricsGrid metrics={session.metrics} />
          </div>
          <aside className="side-column">
            <ControlPanel
              isMonitoring={session.isMonitoring}
              onStart={session.startMonitoring}
              onStop={session.stopMonitoring}
            />
            <EventLog events={session.events} />
          </aside>
        </section>
        <footer className="footer">SMART STUDY MONITOR <span>•</span> FRONTEND PROTOTYPE <span>•</span> v0.1</footer>
      </div>
    </main>
  )
}
