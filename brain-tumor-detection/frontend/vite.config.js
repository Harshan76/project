import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import net from 'node:net'

// Dual-stack bridge plugin for Windows to support both IPv4 (127.0.0.1) and IPv6 (::1 / localhost)
function dualStackPlugin() {
  return {
    name: 'vite-plugin-dual-stack',
    configureServer(server) {
      server.httpServer?.once('listening', () => {
        const address = server.httpServer.address()
        if (address && typeof address === 'object') {
          const port = address.port
          try {
            const s6 = net.createServer(socket => {
              const client = net.connect(port, '127.0.0.1')
              socket.pipe(client).pipe(socket)
              socket.on('error', () => {})
              client.on('error', () => {})
            })
            s6.on('error', () => {})
            s6.listen(port, '::1', () => {
              console.log(`[dual-stack] IPv6 bridge listening on http://[::1]:${port} (supports localhost:${port})`)
            })
            server.httpServer.once('close', () => {
              try { s6.close() } catch (e) {}
            })
          } catch (e) {
            // Ignore if IPv6 is not available
          }
        }
      })
    }
  }
}

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), dualStackPlugin()],
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
