import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    tailwindcss(),
    react()
  ],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:4488',
        changeOrigin: true
      },
      '/media': {
        target: 'http://127.0.0.1:4488',
        changeOrigin: true
      },
      '/projects': {
        target: 'http://127.0.0.1:4488',
        changeOrigin: true
      }
    }
  }
})
