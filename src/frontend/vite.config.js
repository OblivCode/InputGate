import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  // Keep built assets relative so the desktop window can load dist/index.html.
  base: './',
  plugins: [react()],
})
