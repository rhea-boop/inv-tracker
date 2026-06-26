import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: true, // Exposes it to the network automatically
    proxy: {
      // Forward all API calls to Node
      '/api': 'http://localhost:3000',
      // Forward WebSocket traffic to Node
      '/socket.io': {
        target: 'http://localhost:3000',
        ws: true
      }
    }
  }
})