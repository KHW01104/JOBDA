import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      manifest: {
        name: "JOBDA",
        short_name: "JOBDA",
        description: "개인용 채용공고 통합 대시보드",
        theme_color: "#1c2421",
        background_color: "#f4f6f1",
        display: "standalone",
        icons: [{ src: "/jobda-icon.svg", sizes: "any", type: "image/svg+xml", purpose: "any maskable" }],
      },
      workbox: { importScripts: ["push-handler.js"] },
    }),
  ],
});
