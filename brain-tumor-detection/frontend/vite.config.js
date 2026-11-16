import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
      '/uploads': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
      '/enhanced_images': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
      '/reports': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
      '/sample_mris': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      }
    }
  }
})
