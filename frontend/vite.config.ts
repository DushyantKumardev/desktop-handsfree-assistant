import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

function neutralinoGlobalsPlugin(): Plugin {
  return {
    name: "neutralino-globals-plugin",
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        if (req.url === "/__neutralino_globals.js") {
          try {
            const authPath = path.resolve(__dirname, "../app/.tmp/auth_info.json");
            if (fs.existsSync(authPath)) {
              const auth = JSON.parse(fs.readFileSync(authPath, "utf-8"));
              const globalsCode = `
window.NL_PORT = ${auth.nlPort};
window.NL_TOKEN = "${auth.nlToken}";
window.NL_CONNECT_TOKEN = "${auth.nlConnectToken}";
window.NL_ARGS = [];
window.NL_PATH = "..";
window.NL_APPID = "com.handsfree.assistant";
window.NL_MODE = "window";
window.NL_VERSION = "6.10.0";
window.NL_CVERSION = "6.10.0";
`;
              res.setHeader("Content-Type", "application/javascript");
              res.end(globalsCode);
              return;
            }
          } catch (err) {
            console.error("[Vite] Failed to serve Neutralino globals:", err);
          }
        }
        next();
      });
    },
  };
}

export default defineConfig({
  plugins: [react(), tailwindcss(), neutralinoGlobalsPlugin()],
  server: {
    port: 5173,
    strictPort: true,
  },
});
