import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { ErrorBoundary } from './components/ErrorBoundary'
import HomePage from './pages/HomePage'
import WorkspacePage from './pages/WorkspacePage'
import { ThemeProvider } from './context/ThemeContext'
import { validateEnvironment } from './config/environment'
import { Logger } from './utils/logger'

// Validate environment on startup
try {
  validateEnvironment()
} catch (error) {
  const logger = new Logger('App')
  logger.error('Environment validation failed:', error)
  console.error('Environment validation failed:', error)
}

function App() {
  return (
    <ThemeProvider>
    <ErrorBoundary>
      <Router>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/workspace/:projectId" element={<WorkspacePage />} />
        </Routes>
      </Router>
    </ErrorBoundary>
    </ThemeProvider>
  )
}

export default App