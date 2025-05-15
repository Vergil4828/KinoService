import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    host: '0.0.0.0', 
    port: 5173, 
    strictPort: true, 
    hmr: {
      host: 'vosmerka228.ru', 
      clientPort: 443 
    },
    watch: {
      usePolling: true, 
      interval: 1000 
    },
    allowedHosts: [
      'vosmerka228.ru',
      'www.vosmerka228.ru',
      'localhost'
    ],
    cors: true,
    proxy: {
      '/api': {
        target: 'http://backend:3005',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
        secure: false
      }
    }
  },
  
})