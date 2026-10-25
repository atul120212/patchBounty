import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "ui_bundle",
    emptyOutDir: true
  },
  server: {
    host: "0.0.0.0",
    port: 5174,
    proxy: {
      "/api": "http://127.0.0.1:8002",
      "/ws": {
        target: "ws://127.0.0.1:8002",
        ws: true
      }
    }
  }
});
