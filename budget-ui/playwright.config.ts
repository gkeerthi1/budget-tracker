import { defineConfig, devices } from '@playwright/test';

/**
 * Before running these tests, make sure BOTH servers are already running:
 *   Terminal 1: cd backend    && python3 app.py     (http://localhost:5000)
 *   Terminal 2: cd budget-ui  && npm start           (http://localhost:4200)
 *
 * We don't auto-start them here because the backend lives in a separate
 * project folder outside budget-ui - keeping the two processes manual and
 * visible makes failures much easier to diagnose than a silently-managed
 * webServer block, especially when debugging on a teammate's machine.
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: false, // tests share one backend + SQLite file; run serially to avoid cross-test interference
  retries: 0,
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: 'http://localhost:4200',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
