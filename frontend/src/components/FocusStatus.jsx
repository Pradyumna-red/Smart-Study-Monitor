export function FocusStatus({ isMonitoring }) {
  return <section className={`focus-status ${isMonitoring ? 'active' : ''}`}><div className="focus-pulse" /><div><p>OVERALL STATUS</p><h2>{isMonitoring ? 'FOCUS MODE ACTIVE' : 'AWAITING SESSION'}</h2></div><span>{isMonitoring ? 'MONITORING LIVE' : 'SYSTEM IDLE'}</span></section>
}
