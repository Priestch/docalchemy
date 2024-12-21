import { defineConfig } from "vite";
import path from "path";
import { viteStaticCopy } from "vite-plugin-static-copy";
import litestar from "litestar-vite-plugin";
import vue from '@vitejs/plugin-vue';
import ElementPlus from 'unplugin-element-plus/vite'

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
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      }
    }
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
    viteStaticCopy({
      targets: [
        {
          src: path.resolve(__dirname, "node_modules/@document-kits/viewer/dist/generic/*"),
          dest: "document-viewer",
        },
      ],
    }),
    ElementPlus(),
  ],
  resolve: {
    alias: [
      {
        find: /^canvas$/,
        replacement: path.resolve(__dirname, "resources/canvas.js"),
      },
    ],
  },
  css: {
    preprocessorOptions: {
      scss: {api: 'modern-compiler'},
    }
  },
  build: {
    emptyOutDir: true,
    minify: false,
    sourcemap: true,
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
