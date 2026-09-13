import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
   preview: {
    allowedHosts: ['.railway.internal', '.up.railway.app'],
  },
})
