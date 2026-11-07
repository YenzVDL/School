import { defineConfig } from "@playwright/test";
import base from "./playwright.config";
export default defineConfig({
  ...base,
  use: {...base.use, baseURL: "http://127.0.0.1:5173"},
  webServer: {
    ...base.webServer as object,
    command: '"../.venv/Scripts/python.exe" -m uvicorn backend.main:app --app-dir .. --host 127.0.0.1 --port 5173',
    url: "http://127.0.0.1:5173/api/health",
    reuseExistingServer: false,
    env: {RESEARCH_DB: `../tmp/script-browser-${Date.now()}.sqlite3`},
  },
});
