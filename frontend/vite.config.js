import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Frontend for the Budget Notebook. Built to static files that the Pi
// (FastAPI) serves directly; the browser does all the rendering.
// In dev, /api is proxied to the local FastAPI server so the app can use
// same-origin relative URLs in both dev and production.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
