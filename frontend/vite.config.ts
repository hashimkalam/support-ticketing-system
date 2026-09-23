import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: true,
    port: 5173,
    // Bind mounts don't forward filesystem events into the container, so HMR
    // needs polling to notice host edits.
    watch: { usePolling: true },
  },
})
