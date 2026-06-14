import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import litestar from "litestar-vite-plugin";

const ASSET_URL = process.env.ASSET_URL || "/static/";
const VITE_PORT = process.env.VITE_PORT || "5173";
const VITE_HOST = process.env.VITE_HOST || "localhost";

export default defineConfig({
  base: `${ASSET_URL}`,
  root: "resources/",
  clearScreen: false,
  publicDir: "public/",
  resolve: {
    alias: {
      canvas: "",
    },
  },
  server: {
    host: "0.0.0.0",
    port: +`${VITE_PORT}`,
    cors: true,
    hmr: {
      host: `${VITE_HOST}`,
    },
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  plugins: [
    react(),
    tailwindcss(),
    litestar({
      input: ["resources/index.html"],
      assetUrl: `${ASSET_URL}`,
      bundleDirectory: "../src/app/domain/web/public",
      resourceDirectory: "resources",
      hotFile: "src/app/domain/web/public/hot",
    }),
  ],
  build: {
    emptyOutDir: true,
    minify: false,
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes("node_modules")) {
            return "vendor";
          }
        },
      },
    },
  },
});
