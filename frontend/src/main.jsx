import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'sonner'
import App from './App.jsx'
import ErrorBoundary from './components/ErrorBoundary.jsx'
import { AuthProvider } from './context/AuthContext.jsx'
import { ConfigProvider } from './context/ConfigContext.jsx'
import './index.css'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ErrorBoundary>
      <BrowserRouter>
        <ConfigProvider>
          <AuthProvider>
            <App />
            <Toaster richColors position="top-right" closeButton />
          </AuthProvider>
        </ConfigProvider>
      </BrowserRouter>
    </ErrorBoundary>
  </StrictMode>,
)
