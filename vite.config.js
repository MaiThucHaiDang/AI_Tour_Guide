import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import basicSsl from '@vitejs/plugin-basic-ssl'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), basicSsl()],
  server: {
    host: true,
    // Proxy: forward API calls từ HTTPS frontend → HTTP backend (tránh Mixed Content)
    proxy: {
      '/api/v1': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
        // Preserve Content-Type header nguyên vẹn (quan trọng cho multipart/form-data)
        configure: (proxy) => {
          proxy.on('proxyReq', (proxyReq, req) => {
            if (req.headers['content-type']) {
              proxyReq.setHeader('content-type', req.headers['content-type']);
            }
          });
        },
      },
      '/api/voice': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
        secure: false,
        // Preserve Content-Type header nguyên vẹn (quan trọng cho multipart/form-data)
        configure: (proxy) => {
          proxy.on('proxyReq', (proxyReq, req) => {
            if (req.headers['content-type']) {
              proxyReq.setHeader('content-type', req.headers['content-type']);
            }
          });
        },
      },
    },
  },
})
