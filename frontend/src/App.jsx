import Dashboard from './components/Dashboard'
import './App.css'

export default function App() {
  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <div className="header-title">
            <span className="header-icon">☀️</span>
            <div>
              <h1>SolarCast</h1>
              <p>Track and predict your solar energy performance</p>
            </div>
          </div>
          <div className="header-date">
            {new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
          </div>
        </div>
      </header>
      <main className="main">
        <Dashboard />
      </main>
    </div>
  )
}
