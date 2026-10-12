import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { cpSync, mkdirSync } from "node:fs";

export default defineConfig({
  plugins: [react(), {
    name: "local-pdf-assets",
    closeBundle() {
      mkdirSync("dist/pdf-assets", {recursive: true});
      for (const asset of ["cmaps", "standard_fonts", "wasm"]) cpSync(`node_modules/pdfjs-dist/${asset}`, `dist/pdf-assets/${asset}`, {recursive: true});
      cpSync("node_modules/pdfjs-dist/LICENSE", "dist/pdf-assets/LICENSE");
    },
  }],
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
  server: {
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true },
      "/ws": { target: "ws://localhost:8000", ws: true },
      "/health": { target: "http://localhost:8000", changeOrigin: true },
    },
  },
});
