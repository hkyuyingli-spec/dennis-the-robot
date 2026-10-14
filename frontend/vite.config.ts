import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "VITE_");
  const apiBaseUrl = env.VITE_API_BASE_URL?.trim();
  let isSecureApiUrl = false;
  if (apiBaseUrl) {
    try {
      isSecureApiUrl = new URL(apiBaseUrl).protocol === "https:";
    } catch {
      isSecureApiUrl = false;
    }
  }

  if (mode === "android" && !isSecureApiUrl) {
    throw new Error(
      "Android builds require VITE_API_BASE_URL to be an HTTPS backend URL."
    );
  }

  return {
    plugins: [react()],
    base: "./",
    server: {
      host: "0.0.0.0",
      port: 5173,
      proxy: {
        "/api": {
          target: env.VITE_DEV_API_ORIGIN || "http://127.0.0.1:8000",
          changeOrigin: true
        }
      }
    },
    define: {
      __NUTRIBOT_API_BASE_URL__: JSON.stringify(apiBaseUrl || "")
    },
    build: {
      sourcemap: false
    }
  };
});
