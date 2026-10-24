import {defineConfig} from '@playwright/test';

export default defineConfig({
  testDir: './tests/browser',
  timeout: 45_000,
  expect: {timeout: 8_000},
  fullyParallel: false,
  workers: 1,
  reporter: 'line',
  use: {
    browserName: 'chromium',
    headless: true,
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  webServer: [
    {
      command: 'python3 -m http.server 8795 --bind 127.0.0.1 --directory .',
      url: 'http://127.0.0.1:8795/',
      reuseExistingServer: true,
    },
    {
      command: 'python3 -m http.server 8796 --bind 127.0.0.1 --directory dist',
      url: 'http://127.0.0.1:8796/',
      reuseExistingServer: true,
    },
  ],
  projects: [
    {name: 'source', use: {baseURL: 'http://127.0.0.1:8795/'}},
    {name: 'dist', use: {baseURL: 'http://127.0.0.1:8796/'}},
  ],
});
