import { defineConfig } from "vite"
import path from "path"
import litestar from "litestar-vite-plugin"
import vue from '@vitejs/plugin-vue'

const ASSET_URL = process.env.ASSET_URL || "/static/"
const VITE_PORT = process.env.VITE_PORT || "5173"
const VITE_HOST = process.env.VITE_HOST || "localhost"
export default defineConfig({
  base: `${ASSET_URL}`,
  root: "resources/",
  clearScreen: false,
  publicDir: "public/",
  server: {
    host: "0.0.0.0",
    port: +`${VITE_PORT}`,
    cors: true,
    hmr: {
      host: `${VITE_HOST}`,
    },
  },
  plugins: [
    vue(),
    litestar({
      input: ["resources/index.html"],
      assetUrl: `${ASSET_URL}`,
      bundleDirectory: "../src/app/domain/web/public",
      resourceDirectory: "resources",
      hotFile: "src/app/domain/web/public/hot",
    }),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "resources"),
    },
  },
  build: {
    emptyOutDir: true,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes("node_modules")) {
            return "vendor"
          }
        },
      },
    },
  },
})
