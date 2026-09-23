import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: true,
    port: 5173,
    // Fail loudly instead of quietly moving to 5174, which would no longer be a
    // CORS-allowed origin and would break every API call with an opaque error.
    strictPort: true,
    // Bind mounts don't forward filesystem events into the container, so HMR
    // needs polling to notice host edits.
    watch: { usePolling: true },
  },
})
