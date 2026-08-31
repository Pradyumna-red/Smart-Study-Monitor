export function Header({ isMonitoring }) {
  return <header className="header"><div className="brand"><span className="brand-mark">◈</span><div><p className="eyebrow">NEURAL FOCUS PROTOCOL</p><h1>SMART STUDY <em>MONITOR</em></h1></div></div><div className={`system-status ${isMonitoring ? 'active' : ''}`}><span className="status-dot" /> SYSTEM {isMonitoring ? 'ONLINE' : 'STANDBY'}</div></header>
}
