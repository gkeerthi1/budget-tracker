import { Page, expect } from '@playwright/test';

/**
 * Generates a fresh, never-seen-before email for each test. Each Playwright
 * test run starts against whatever is already in budget_tracker.db, so
 * reusing a fixed email across runs would collide with a previous run's
 * account (register returns 409 for a duplicate email). A timestamp +
 * random suffix keeps every test isolated from every other test and from
 * previous runs, without needing to reset the database between runs.
 */
export function freshEmail(prefix = 'e2e'): string {
  return `${prefix}-${Date.now()}-${Math.floor(Math.random() * 100000)}@test.com`;
}

export const TEST_PASSWORD = 'pw12345';

/** Registers a brand-new account, then logs in with it, landing on the dashboard. */
export async function registerAndLogin(page: Page, email: string, password = TEST_PASSWORD) {
  await page.goto('/login');
  await page.getByTestId('toggle-mode').click(); // switch to Register mode
  await page.getByTestId('email-input').fill(email);
  await page.getByTestId('password-input').fill(password);
  await page.getByTestId('submit-btn').click();

  // Login component auto-logs-in right after a successful register,
  // so we should land on the dashboard without a second manual login.
  await expect(page).toHaveURL(/.*dashboard/);
}

/**
 * Clicks a nav link to move between pages while logged in, instead of
 * page.goto(). page.goto() forces a full browser reload, which wipes the
 * in-memory "logged in" flag the app uses (AuthService.loggedIn is a plain
 * signal, not persisted) even though the session cookie is still valid on
 * the backend - the route guard then bounces to /login. A real user never
 * hits this because they click links, not the address bar, so tests should
 * do the same.
 */
export async function goToTab(page: Page, tab: 'dashboard' | 'categories' | 'transactions' | 'recurring' | 'goals') {
  await page.getByTestId(`nav-${tab}`).click();
  await expect(page).toHaveURL(new RegExp(`.*${tab}`));
}

/** Adds a category via the Categories page. Assumes the caller is already logged in. */
export async function addCategory(page: Page, name: string, budget: number) {
  await goToTab(page, 'categories');
  await page.getByTestId('category-name-input').fill(name);
  await page.getByTestId('category-budget-input').fill(String(budget));
  await page.getByTestId('add-category-btn').click();
  await expect(page.getByTestId('category-table')).toContainText(name);
}

/**
 * Today's date as yyyy-mm-dd using LOCAL time, matching the app's own
 * localDateIso() in transactions.component.ts. Using toISOString() here
 * would convert to UTC, which rolls over to "tomorrow" every evening in
 * any timezone behind UTC (e.g. US Eastern) - the backend then rejects
 * the date as being in the future. This was a real bug caught by these
 * tests, not just a test-authoring mistake.
 */
export function todayIso(): string {
  const d = new Date();
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}
