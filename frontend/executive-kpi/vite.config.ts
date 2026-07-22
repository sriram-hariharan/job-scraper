import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

const projectDir = dirname(fileURLToPath(import.meta.url));

export default defineConfig(({ command }) => ({
  plugins: [react()],
  define: command === "build"
    ? { "process.env.NODE_ENV": JSON.stringify("production") }
    : {},
  build: {
    target: "es2018",
    outDir: resolve(projectDir, "../../src/app/static/build/executive-kpi"),
    emptyOutDir: true,
    cssCodeSplit: false,
    lib: {
      entry: resolve(projectDir, "src/main.tsx"),
      name: "ApplyLensExecutiveKpi",
      formats: ["es"],
      fileName: () => "executive-kpi.js",
    },
    rollupOptions: {
      output: {
        assetFileNames: (assetInfo) =>
          assetInfo.name?.endsWith(".css") ? "executive-kpi.css" : "[name][extname]",
      },
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
  },
}));
