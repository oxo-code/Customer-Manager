import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';

const backendTarget = 'http://127.0.0.1:8001';

export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    watch: {
      ignored: [
        '**/output/**',
        '**/public/**',
        '**/backend/.local/**',
        '**/__pycache__/**',
        '**/mso*.tmp',
        '**/~$*',
      ],
    },
    proxy: {
      '/api': {
        target: backendTarget,
        changeOrigin: true,
        secure: false,
      },
    },
  },
  preview: {
    host: '127.0.0.1',
    port: 4173,
    proxy: {
      '/api': {
        target: backendTarget,
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
