import { defineConfig } from "vite";
import { viteStaticCopy } from "vite-plugin-static-copy";

export default defineConfig({
  plugins: [
    viteStaticCopy({
      targets: [
        {
          src: "node_modules/@document-kits/viewer/dist/generic/*",
          dest: "document-viewer",
        },
      ],
    }),
  ],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
    }
  },
  // optimizeDeps: {
  //   include: ["@document-kits/viewer"],
  // },
  // build: {
  //   commonjsOptions: {
  //     include: [/document-viewer/],
  //   },
  // },
  // base: "/document-viewer/demos/",
  resolve: {
    alias: [
      {
        find: /^canvas$/,
        replacement: "canvas.js",
      },
    ],
  },
});
