import { test, expect } from '@playwright/test';
import { freshEmail, TEST_PASSWORD } from './helpers';

/**
 * Covers the proposal's V1 system testing commitment:
 * "logging in with existing and non-existing accounts"
 */
test.describe('Authentication', () => {
  test('registering a new account logs the user in and reaches the dashboard', async ({ page }) => {
    const email = freshEmail('register');

    await page.goto('/login');
    await page.getByTestId('toggle-mode').click();
    await expect(page.getByRole('heading', { name: 'Create account' })).toBeVisible();

    await page.getByTestId('email-input').fill(email);
    await page.getByTestId('password-input').fill(TEST_PASSWORD);
    await page.getByTestId('submit-btn').click();

    await expect(page).toHaveURL(/.*dashboard/);
    await expect(page.getByTestId('nav-bar')).toBeVisible();
  });

  test('registering with an email that already exists shows an error', async ({ page }) => {
    const email = freshEmail('dup');

    // First registration succeeds.
    await page.goto('/login');
    await page.getByTestId('toggle-mode').click();
    await page.getByTestId('email-input').fill(email);
    await page.getByTestId('password-input').fill(TEST_PASSWORD);
    await page.getByTestId('submit-btn').click();
    await expect(page).toHaveURL(/.*dashboard/);

    // Log out, then try registering the SAME email again.
    await page.getByTestId('logout-btn').click();
    await expect(page).toHaveURL(/.*login/);

    await page.getByTestId('toggle-mode').click();
    await page.getByTestId('email-input').fill(email);
    await page.getByTestId('password-input').fill(TEST_PASSWORD);
    await page.getByTestId('submit-btn').click();

    await expect(page.getByTestId('auth-error')).toBeVisible();
    await expect(page).toHaveURL(/.*login/); // never left the login page
  });

  test('logging in with an existing account succeeds', async ({ page }) => {
    const email = freshEmail('existing');

    // Register once, then log out.
    await page.goto('/login');
    await page.getByTestId('toggle-mode').click();
    await page.getByTestId('email-input').fill(email);
    await page.getByTestId('password-input').fill(TEST_PASSWORD);
    await page.getByTestId('submit-btn').click();
    await expect(page).toHaveURL(/.*dashboard/);
    await page.getByTestId('logout-btn').click();

    // Log back in with the same credentials (mode defaults to "Log in").
    await page.getByTestId('email-input').fill(email);
    await page.getByTestId('password-input').fill(TEST_PASSWORD);
    await page.getByTestId('submit-btn').click();

    await expect(page).toHaveURL(/.*dashboard/);
  });

  test('logging in with a non-existing account shows an error and stays on login', async ({ page }) => {
    await page.goto('/login');
    await page.getByTestId('email-input').fill(freshEmail('never-registered'));
    await page.getByTestId('password-input').fill('whatever-password');
    await page.getByTestId('submit-btn').click();

    await expect(page.getByTestId('auth-error')).toBeVisible();
    await expect(page).toHaveURL(/.*login/);
  });

  test('logging in with the wrong password for an existing account shows an error', async ({ page }) => {
    const email = freshEmail('wrongpw');

    await page.goto('/login');
    await page.getByTestId('toggle-mode').click();
    await page.getByTestId('email-input').fill(email);
    await page.getByTestId('password-input').fill(TEST_PASSWORD);
    await page.getByTestId('submit-btn').click();
    await expect(page).toHaveURL(/.*dashboard/);
    await page.getByTestId('logout-btn').click();

    await page.getByTestId('email-input').fill(email);
    await page.getByTestId('password-input').fill('totally-wrong-password');
    await page.getByTestId('submit-btn').click();

    await expect(page.getByTestId('auth-error')).toBeVisible();
    await expect(page).toHaveURL(/.*login/);
  });

  test('visiting a protected page while logged out redirects to login', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/.*login/);

    await page.goto('/categories');
    await expect(page).toHaveURL(/.*login/);
  });

  test('logging out returns to login and re-protects the app', async ({ page }) => {
    const email = freshEmail('logout');

    await page.goto('/login');
    await page.getByTestId('toggle-mode').click();
    await page.getByTestId('email-input').fill(email);
    await page.getByTestId('password-input').fill(TEST_PASSWORD);
    await page.getByTestId('submit-btn').click();
    await expect(page).toHaveURL(/.*dashboard/);

    await page.getByTestId('logout-btn').click();
    await expect(page).toHaveURL(/.*login/);

    // Nav bar (only shown when logged in) should be gone.
    await expect(page.getByTestId('nav-bar')).toHaveCount(0);
  });
});
