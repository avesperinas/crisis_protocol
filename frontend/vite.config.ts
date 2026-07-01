import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  // Fail loudly if 5173 is taken instead of silently picking another port —
  // the backend's CORS allowlist is pinned to this exact origin. Bind IPv4
  // explicitly: on machines where "localhost" resolves to ::1 first, Vite's
  // bare default can end up IPv6-only, which silently breaks anything that
  // hits it via 127.0.0.1.
  server: { port: 5173, strictPort: true, host: '127.0.0.1' },
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'Crisis Protocol',
        short_name: 'Crisis Protocol',
        description: 'Negociación geopolítica multijugador con IA',
        lang: 'es',
        start_url: '/',
        display: 'standalone',
        background_color: '#0d0d0f',
        theme_color: '#0d0d0f',
        icons: [
          { src: '/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icon-512.png', sizes: '512x512', type: 'image/png' },
          { src: '/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        // App-shell only: game/API data is never cached, so players always see
        // live state. Only the static build assets are precached for offline load.
        globPatterns: ['**/*.{js,css,html,svg,png}'],
        navigateFallbackDenylist: [/^\/api\//, /^\/ws\//],
      },
    }),
  ],
})
