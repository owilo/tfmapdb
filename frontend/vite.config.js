import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from "path"
import tsconfigPaths from "vite-tsconfig-paths";

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    tsconfigPaths()
  ],
  server: {
    /*host: true,
    allowedHosts: [
      ".ngrok-free.app"
    ],*/
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false
      }
    },
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "src"),
      }
    }
  }
})