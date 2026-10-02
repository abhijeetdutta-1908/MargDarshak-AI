import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: Number(process.env.PORT) || 5173,
    // Same-origin /api in dev, mirrors the nginx proxy in Docker.
    proxy: { '/api': process.env.VITE_PROXY_TARGET || 'http://localhost:8000' },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.js'],
    css: false,
  },
})
