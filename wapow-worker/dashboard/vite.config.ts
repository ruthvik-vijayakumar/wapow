import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    tailwindcss(),
  ],
  build: {
    outDir: '../scraper/dist',
    emptyOutDir: true
  },
  server: {
    port: 5173,
    proxy: {
      '/jobs': 'http://127.0.0.1:3003',
      '/worker': 'http://127.0.0.1:3003',
      '/sources': 'http://127.0.0.1:3003',
      '/health': 'http://127.0.0.1:3003',
      '/config': 'http://127.0.0.1:3003',
      '/api': {
        target: 'http://127.0.0.1:3003',
        changeOrigin: true,
      }
    }
  }
})

