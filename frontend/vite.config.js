import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return undefined;

          if (id.includes('react-router-dom') || id.includes('react-router') || id.includes('@remix-run')) {
            return 'vendor-router';
          }

          if (id.includes('i18next') || id.includes('react-i18next')) {
            return 'vendor-i18n';
          }

          if (id.includes('framer-motion')) {
            return 'vendor-motion';
          }

          if (id.includes('lucide-react')) {
            return 'vendor-icons';
          }

          if (id.includes('remotion') || id.includes('@remotion')) {
            return 'vendor-remotion';
          }

          if (id.includes('axios') || id.includes('@react-oauth')) {
            return 'vendor-api';
          }

          if (
            /node_modules[/\\](react|react-dom|scheduler|use-sync-external-store)[/\\]/.test(id)
          ) {
            return 'vendor-react';
          }

          return 'vendor';
        },
      },
    },
  },
})
