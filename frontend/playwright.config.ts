import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  timeout: 90_000,
  fullyParallel: false,
  workers: 1,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:4173",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    ...devices["Desktop Chrome"],
  },
  webServer: [
    {
      command: "bash ../scripts/start-test-backend.sh",
      url: "http://127.0.0.1:18000/api/v1/health",
      timeout: 60_000,
      reuseExistingServer: false,
    },
    {
      command:
        "VITE_API_URL=http://127.0.0.1:18000/api/v1 npm run dev -- --host 127.0.0.1 --port 4173",
      url: "http://127.0.0.1:4173/login",
      timeout: 60_000,
      reuseExistingServer: false,
    },
  ],
});
