/// <reference types="vitest" />
import path from 'path'

import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
  },
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
      '@/app': path.resolve(import.meta.dirname, './src/app'),
      '@/core': path.resolve(import.meta.dirname, './src/core'),
      '@/shared': path.resolve(import.meta.dirname, './src/shared'),
      '@/features': path.resolve(import.meta.dirname, './src/features'),
      '@/theme': path.resolve(import.meta.dirname, './src/theme'),
      '@/types': path.resolve(import.meta.dirname, './src/types'),
      '@/tests': path.resolve(import.meta.dirname, './src/tests'),
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/tests/setupTests.ts'],
  },
})