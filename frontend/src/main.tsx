import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '@fontsource/playfair-display/latin-400.css'
import '@fontsource/playfair-display/latin-700.css'
import '@fontsource/source-sans-3/latin-400.css'
import '@fontsource/source-sans-3/latin-600.css'
import '@fontsource/source-sans-3/latin-700.css'
import './styles.css'
import App from './App'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
